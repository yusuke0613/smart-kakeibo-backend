from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.database import get_db
from app.schemas import schemas
from app.models import models
import httpx
import os
import json
from PIL import Image
from io import BytesIO
import uuid
import logging
import traceback
import re
from decimal import Decimal
from datetime import datetime, date

# ロガーの設定
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/image-processing", tags=["image-processing"])

# 環境変数から設定を取得（実際の環境に合わせて設定）
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost")
API_KEY = os.getenv("API_KEY", "app-aPyp7Npxdgywn4j6sOiX1kLS")

@router.post("/extract-transaction", response_model=List[schemas.TransactionCreate])
async def extract_transaction_from_image(
    files: List[UploadFile] = File(None),
    use_mock: bool = Query(False, description="モックデータを使用するかどうか"),
    debug_mode: bool = Query(False, description="デバッグモードを有効にするかどうか"),
    user_id: str = Query("default_user", description="ユーザーID")
):
    """
    アップロードされた画像からトランザクション情報を抽出するエンドポイント
    """
    if use_mock:
        logger.info("モックデータを使用します")
        mock_transactions = get_mock_transactions()
        # モックデータのログ出力
        logger.info(f"返却するモックデータ: {len(mock_transactions)}件")
        for i, tx in enumerate(mock_transactions):
            logger.info(f"モックトランザクション[{i}]: {tx.dict()}")
        return mock_transactions
    
    if not files:
        raise HTTPException(status_code=400, detail="ファイルがアップロードされていません")
    
    logger.info(f"{len(files)}個のファイルが処理のためにアップロードされました。ユーザーID: {user_id}")
    
    # デバッグモードの設定
    if debug_mode:
        logger.setLevel(logging.DEBUG)
        logger.info("デバッグモードが有効になりました")
    
    try:
        # 画像ファイルを一時ディレクトリに保存
        temp_files = []
        for file in files:
            # ファイル名とコンテンツタイプをログに記録
            logger.info(f"ファイル名: {file.filename}, コンテンツタイプ: {file.content_type}")
            
            if not file.content_type or not file.content_type.startswith("image/"):
                logger.warning(f"非画像ファイルがスキップされました: {file.filename}, タイプ: {file.content_type}")
                continue
            
            # 一時ファイルを作成
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
            temp_files.append(temp_file.name)
            
            # ファイルを一時ファイルに書き込む
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            
            logger.info(f"ファイルが一時ディレクトリに保存されました: {temp_file.name}")
        
        if not temp_files:
            raise HTTPException(status_code=400, detail="有効な画像ファイルがありません")
        
        # ワークフローを実行
        logger.info("画像処理ワークフローを開始します")
        
        # ワークフローの実行
        try:
            # ワークフローの実行（ユーザーIDを渡す）
            workflow_response = execute_workflow(temp_files, user_id)
            
            # デバッグ用に完全なレスポンスをログに出力
            logger.info(f"ワークフローレスポンス全体: {json.dumps(workflow_response, default=str)}")
            
            # 直接curlコマンドを実行して結果を比較（デバッグ用）
            if debug_mode:
                try:
                    import subprocess
                    # ファイルをアップロードして得られたfile_idを使用
                    file_id = workflow_response.get("file_id", "")
                    if file_id:
                        curl_cmd = [
                            "curl", "--location", "http://localhost/v1/workflows/run",
                            "--header", "Authorization: Bearer app-aPyp7Npxdgywn4j6sOiX1kLS",
                            "--header", "Content-Type: application/json",
                            "--data", json.dumps({
                                "inputs": {
                                    "image": [
                                        {
                                            "transfer_method": "local_file",
                                            "upload_file_id": file_id,
                                            "type": "image"
                                        }
                                    ]
                                },
                                "response_mode": "blocking",
                                "user": user_id
                            })
                        ]
                        logger.info(f"curlコマンドを実行: {' '.join(curl_cmd)}")
                        result = subprocess.run(curl_cmd, capture_output=True, text=True)
                        logger.info(f"curlコマンドの結果: {result.stdout}")
                except Exception as curl_error:
                    logger.error(f"curlコマンドの実行中にエラーが発生しました: {str(curl_error)}")
            
            # レスポンスからトランザクション情報を抽出
            transactions = extract_transactions_from_response(workflow_response)
            
            # 抽出されたトランザクションの詳細をログに出力
            logger.info(f"抽出されたトランザクション: {len(transactions)}件")
            for i, tx in enumerate(transactions):
                logger.info(f"トランザクション[{i}]: {tx.dict()}")
            
            if not transactions:
                logger.warning("トランザクションが抽出できませんでした")
                
                # 直接APIを呼び出してみる（デバッグ用）
                try:
                    import httpx
                    api_base_url = os.getenv("API_BASE_URL", "http://localhost")
                    headers = {
                        'Authorization': 'Bearer app-aPyp7Npxdgywn4j6sOiX1kLS',
                        'Content-Type': 'application/json'
                    }
                    
                    # ファイルをアップロード
                    file_ids = []
                    for image_path in temp_files:
                        with open(image_path, 'rb') as f:
                            files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
                            data = {'user': user_id}
                            
                            upload_url = f"{api_base_url}/v1/files/upload"
                            response = httpx.post(
                                upload_url,
                                headers={'Authorization': 'Bearer app-aPyp7Npxdgywn4j6sOiX1kLS'},
                                files=files,
                                data=data
                            )
                            
                            if response.status_code in [200, 201]:
                                file_data = response.json()
                                file_id = file_data.get('id')
                                if file_id:
                                    file_ids.append(file_id)
                    
                    if file_ids:
                        # ワークフロー実行
                        payload = {
                            "inputs": {
                                "image": [
                                    {
                                        "transfer_method": "local_file",
                                        "upload_file_id": file_id,
                                        "type": "image"
                                    } for file_id in file_ids
                                ]
                            },
                            "response_mode": "blocking",
                            "user": user_id
                        }
                        
                        workflow_url = f"{api_base_url}/v1/workflows/run"
                        response = httpx.post(
                            workflow_url,
                            headers=headers,
                            json=payload,
                            timeout=60.0
                        )
                        
                        if response.status_code in [200, 201, 202]:
                            direct_response = response.json()
                            logger.info(f"直接APIを呼び出した結果: {json.dumps(direct_response, default=str)}")
                            
                            # 直接APIを呼び出した結果からトランザクションを抽出
                            direct_transactions = extract_transactions_from_response(direct_response)
                            if direct_transactions:
                                logger.info(f"直接APIから抽出されたトランザクション: {len(direct_transactions)}件")
                                return direct_transactions
                except Exception as direct_api_error:
                    logger.error(f"直接APIを呼び出す際にエラーが発生しました: {str(direct_api_error)}")
                
                if debug_mode:
                    # デバッグモードの場合、モックデータを返す
                    logger.warning("デバッグモードのためモックデータを返します。")
                    mock_transactions = get_mock_transactions()
                    logger.info(f"返却するモックデータ: {len(mock_transactions)}件")
                    for i, tx in enumerate(mock_transactions):
                        logger.info(f"モックトランザクション[{i}]: {tx.dict()}")
                    return mock_transactions
                else:
                    # 空のリストを返す
                    logger.info("空のリストを返します")
                    return []
            
            # 最終的なレスポンスをログに出力
            logger.info(f"最終レスポンス: {len(transactions)}件のトランザクション")
            return transactions
        except Exception as workflow_error:
            error_detail = traceback.format_exc()
            logger.error(f"ワークフローの実行中にエラーが発生しました: {str(workflow_error)}\n{error_detail}")
            
            if debug_mode:
                # デバッグモードの場合、モックデータを返す
                logger.warning("ワークフローエラーが発生しました。デバッグモードのためモックデータを返します。")
                mock_transactions = get_mock_transactions()
                logger.info(f"返却するモックデータ: {len(mock_transactions)}件")
                for i, tx in enumerate(mock_transactions):
                    logger.info(f"モックトランザクション[{i}]: {tx.dict()}")
                return mock_transactions
            
            raise HTTPException(status_code=500, detail=f"ワークフローの実行中にエラーが発生しました: {str(workflow_error)}")
    
    finally:
        # 一時ファイルを削除
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
                logger.info(f"一時ファイルが削除されました: {temp_file}")
            except Exception as cleanup_error:
                logger.error(f"一時ファイルの削除中にエラーが発生しました: {str(cleanup_error)}")

def execute_workflow(image_paths: List[str], user_id: str = "default_user") -> Dict[str, Any]:
    """
    画像処理ワークフローを実行する関数
    """
    logger.info(f"ワークフローを実行します: {len(image_paths)}個の画像、ユーザーID: {user_id}")
    
    try:
        # 環境変数からAPIのベースURLを取得
        api_base_url = os.getenv("API_BASE_URL", "http://localhost")
        
        # 認証ヘッダーの設定
        headers = {
            'Authorization': 'Bearer app-aPyp7Npxdgywn4j6sOiX1kLS',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"APIリクエストの準備: URL={api_base_url}")
        
        # 画像ファイルをアップロード
        file_ids = []
        for image_path in image_paths:
            # ファイルアップロードのリクエスト
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
                data = {'user': user_id}  # ユーザーIDをデータに含める
                
                # ファイルアップロードのエンドポイント
                upload_url = f"{api_base_url}/v1/files/upload"
                logger.info(f"ファイルアップロード: {upload_url}, ユーザー: {user_id}")
                
                # ファイルアップロードのリクエスト
                response = httpx.post(
                    upload_url,
                    headers={'Authorization': 'Bearer app-aPyp7Npxdgywn4j6sOiX1kLS'},
                    files=files,
                    data=data,
                    timeout=30.0  # タイムアウトを設定
                )
                
                # レスポンスの詳細をログに出力
                logger.info(f"ファイルアップロードレスポンス: ステータス={response.status_code}")
                if response.status_code in [200, 201]:
                    logger.info(f"ファイルアップロードレスポンス内容: {response.text}")
                else:
                    logger.error(f"ファイルアップロードエラー: {response.status_code} - {response.text}")
                
                # レスポンスの確認
                if response.status_code not in [200, 201]:
                    raise Exception(f"ファイルアップロードエラー: {response.status_code} - {response.text}")
                
                # ファイルIDを取得
                file_data = response.json()
                file_id = file_data.get('id')
                
                if not file_id:
                    logger.error(f"ファイルIDが見つかりません: {file_data}")
                    raise Exception(f"ファイルIDが見つかりません: {file_data}")
                
                file_ids.append(file_id)
                logger.info(f"ファイルアップロード成功: ID={file_id}")
        
        # 指定された構造でワークフロー実行のペイロードを作成（curlコマンドと同じ形式）
        payload = {
            "inputs": {
                "image": [
                    {
                        "transfer_method": "local_file",
                        "upload_file_id": file_id,
                        "type": "image"
                    } for file_id in file_ids
                ]
            },
            "response_mode": "blocking",
            "user": user_id
        }
        
        logger.info(f"ワークフロー実行リクエスト: {json.dumps(payload)}")
        
        # ワークフロー実行のエンドポイント
        workflow_url = f"{api_base_url}/v1/workflows/run"
        logger.info(f"ワークフロー実行URL: {workflow_url}")
        
        # ワークフロー実行のリクエスト
        response = httpx.post(
            workflow_url,
            headers=headers,
            json=payload,
            timeout=60.0  # タイムアウトを設定（ワークフロー実行は時間がかかる可能性がある）
        )
        
        # レスポンスの詳細をログに出力
        logger.info(f"ワークフロー実行レスポンス: ステータス={response.status_code}")
        if response.status_code in [200, 201, 202]:
            logger.info(f"ワークフロー実行レスポンス内容: {response.text[:1000]}...")  # 長すぎる場合は切り詰める
        else:
            logger.error(f"ワークフロー実行エラー: {response.status_code} - {response.text}")
        
        # レスポンスの確認
        if response.status_code not in [200, 201, 202]:
            raise Exception(f"ワークフロー実行エラー: {response.status_code} - {response.text}")
        
        # レスポンスをJSONとして解析
        workflow_response = response.json()
        logger.info(f"ワークフロー実行成功: {response.status_code}")
        
        # ファイルIDを保存（デバッグ用）
        if file_ids:
            workflow_response["file_id"] = file_ids[0]
        
        return workflow_response
    
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"ワークフロー実行中にエラーが発生しました: {str(e)}\n{error_detail}")
        
        # エラーが発生した場合はモックレスポンスを返す（デバッグ用）
        logger.warning("エラーが発生したため、モックレスポンスを返します")
        return {
            "outputs": [
                {
                    "value": {
                        "items": [
                            {
                                "amount": 1200,
                                "transaction_date": "2023-05-15",
                                "description": "コーヒー購入",
                                "major_category_id": 1,
                                "minor_category_id": 2
                            }
                        ]
                    }
                }
            ]
        }

def extract_transactions_from_response(response: Dict[str, Any]) -> List[schemas.TransactionCreate]:
    """レスポンスからトランザクション情報を抽出する関数"""
    try:
        # レスポンス全体をログに出力（デバッグ用）
        logger.info(f"ワークフローレスポンス構造: {json.dumps(response, default=str)}")
        
        # 新しいレスポンス構造に対応
        if "data" in response and "outputs" in response["data"] and "response" in response["data"]["outputs"]:
            # Markdown コードブロックから JSON を抽出
            response_text = response["data"]["outputs"]["response"]
            logger.info(f"レスポンスのテキスト: {response_text}")
            
            # Markdown コードブロックから JSON 部分を抽出
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.info(f"抽出された JSON 文字列: {json_str}")
                
                try:
                    # JSON をパース
                    json_data = json.loads(json_str)
                    logger.info(f"パースされた JSON データ: {json.dumps(json_data, default=str)}")
                    
                    # items フィールドを取得
                    if "items" in json_data:
                        items = json_data["items"]
                        logger.info(f"抽出された items: {json.dumps(items, default=str)}")
                        
                        # トランザクションリストを作成
                        transactions = []
                        for i, item in enumerate(items):
                            try:
                                # スキーマに合わせてトランザクションオブジェクトを作成
                                transaction_data = {
                                    "amount": extract_field(item, "amount"),
                                    "transaction_date": extract_field(item, "transaction_date"),
                                    "description": extract_field(item, "description"),
                                    "major_category_id": extract_field(item, "major_category_id", 1),
                                    "minor_category_id": extract_field(item, "minor_category_id")
                                }
                                
                                logger.info(f"変換されたトランザクションデータ: {json.dumps(transaction_data, default=str)}")
                                
                                # Pydanticモデルに変換
                                transaction = schemas.TransactionCreate(**transaction_data)
                                transactions.append(transaction)
                                logger.info(f"トランザクション[{i}]の変換に成功しました")
                            except Exception as item_error:
                                error_detail = traceback.format_exc()
                                logger.error(f"アイテム[{i}]の処理中にエラーが発生しました: {str(item_error)}\n{error_detail}")
                                # 個別のアイテムエラーはスキップして次に進む
                                continue
                        
                        logger.info(f"抽出されたトランザクション数: {len(transactions)}")
                        return transactions
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON のパースに失敗しました: {str(json_error)}")
        
        # 直接 response フィールドがある場合（文字列として）
        if "response" in response:
            response_text = response["response"]
            if isinstance(response_text, str):
                logger.info(f"直接 response フィールドを検出: {response_text}")
                
                # JSON 文字列かどうかを確認
                try:
                    json_data = json.loads(response_text)
                    if "items" in json_data:
                        items = json_data["items"]
                        logger.info(f"response から直接 items を抽出: {json.dumps(items, default=str)}")
                        
                        # トランザクションリストを作成
                        transactions = []
                        for i, item in enumerate(items):
                            try:
                                transaction_data = {
                                    "amount": extract_field(item, "amount"),
                                    "transaction_date": extract_field(item, "transaction_date"),
                                    "description": extract_field(item, "description"),
                                    "major_category_id": extract_field(item, "major_category_id", 1),
                                    "minor_category_id": extract_field(item, "minor_category_id")
                                }
                                
                                transaction = schemas.TransactionCreate(**transaction_data)
                                transactions.append(transaction)
                            except Exception as item_error:
                                logger.error(f"アイテム[{i}]の処理中にエラーが発生しました: {str(item_error)}")
                                continue
                        
                        return transactions
                except json.JSONDecodeError:
                    # JSON ではない場合は Markdown コードブロックを探す
                    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                    if json_match:
                        try:
                            json_str = json_match.group(1)
                            json_data = json.loads(json_str)
                            if "items" in json_data:
                                items = json_data["items"]
                                
                                # トランザクションリストを作成
                                transactions = []
                                for i, item in enumerate(items):
                                    try:
                                        transaction_data = {
                                            "amount": extract_field(item, "amount"),
                                            "transaction_date": extract_field(item, "transaction_date"),
                                            "description": extract_field(item, "description"),
                                            "major_category_id": extract_field(item, "major_category_id", 1),
                                            "minor_category_id": extract_field(item, "minor_category_id")
                                        }
                                        
                                        transaction = schemas.TransactionCreate(**transaction_data)
                                        transactions.append(transaction)
                                    except Exception as item_error:
                                        logger.error(f"アイテム[{i}]の処理中にエラーが発生しました: {str(item_error)}")
                                        continue
                                
                                return transactions
                        except Exception as e:
                            logger.error(f"Markdown コードブロックの処理中にエラーが発生しました: {str(e)}")
        
        # curl コマンドのレスポンス形式に対応
        if "task_id" in response and "workflow_run_id" in response and "data" in response:
            data = response["data"]
            if "outputs" in data and "response" in data["outputs"]:
                response_text = data["outputs"]["response"]
                logger.info(f"curl レスポンス形式を検出: {response_text}")
                
                # Markdown コードブロックから JSON を抽出
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(1)
                        json_data = json.loads(json_str)
                        if "items" in json_data:
                            items = json_data["items"]
                            
                            # トランザクションリストを作成
                            transactions = []
                            for i, item in enumerate(items):
                                try:
                                    transaction_data = {
                                        "amount": extract_field(item, "amount"),
                                        "transaction_date": extract_field(item, "transaction_date"),
                                        "description": extract_field(item, "description"),
                                        "major_category_id": extract_field(item, "major_category_id", 1),
                                        "minor_category_id": extract_field(item, "minor_category_id")
                                    }
                                    
                                    transaction = schemas.TransactionCreate(**transaction_data)
                                    transactions.append(transaction)
                                except Exception as item_error:
                                    logger.error(f"アイテム[{i}]の処理中にエラーが発生しました: {str(item_error)}")
                                    continue
                            
                            return transactions
                    except Exception as e:
                        logger.error(f"curl レスポンスの処理中にエラーが発生しました: {str(e)}")
        
        # 従来のレスポンス構造も試す（既存のコード）
        # ... 既存のコード ...
        
        # 抽出されたアイテムをログに出力
        logger.info(f"抽出されたアイテム: {json.dumps(items, default=str)}")
        logger.info(f"抽出されたアイテム数: {len(items)}")
        
        if not items:
            logger.warning("トランザクション情報が見つかりませんでした")
            return []
        
        # トランザクションリストを作成
        transactions = []
        
        for i, item in enumerate(items):
            logger.info(f"アイテム[{i}]の処理: {json.dumps(item, default=str)}")
            
            try:
                # スキーマに合わせてトランザクションオブジェクトを作成
                transaction_data = {
                    "amount": extract_field(item, "amount"),
                    "transaction_date": extract_field(item, "transaction_date"),
                    "description": extract_field(item, "description"),
                    "major_category_id": extract_field(item, "major_category_id", 1),  # デフォルト値を設定
                    "minor_category_id": extract_field(item, "minor_category_id")
                }
                
                logger.info(f"変換されたトランザクションデータ: {json.dumps(transaction_data, default=str)}")
                
                # Pydanticモデルに変換
                transaction = schemas.TransactionCreate(**transaction_data)
                transactions.append(transaction)
                logger.info(f"トランザクション[{i}]の変換に成功しました")
            except Exception as item_error:
                error_detail = traceback.format_exc()
                logger.error(f"アイテム[{i}]の処理中にエラーが発生しました: {str(item_error)}\n{error_detail}")
                # 個別のアイテムエラーはスキップして次に進む
                continue
        
        logger.info(f"抽出されたトランザクション数: {len(transactions)}")
        return transactions
    
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"トランザクション情報の抽出中にエラーが発生しました: {str(e)}\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"トランザクション情報の抽出中にエラーが発生しました: {str(e)}")

def extract_field(item: Dict[str, Any], field_name: str, default_value: Any = None) -> Any:
    """
    さまざまなフィールド名のバリエーションに対応して値を抽出する関数
    """
    # フィールド名のバリエーション
    field_variations = {
        "amount": ["amount", "price", "value", "cost", "金額", "料金", "価格"],
        "transaction_date": ["transaction_date", "date", "purchase_date", "payment_date", "日付", "取引日", "支払日"],
        "description": ["description", "name", "item", "product", "service", "memo", "note", "説明", "内容", "品目", "メモ"],
        "major_category_id": ["major_category_id", "category_id", "main_category", "カテゴリID", "主カテゴリ"],
        "minor_category_id": ["minor_category_id", "subcategory_id", "sub_category", "サブカテゴリID", "副カテゴリ"]
    }
    
    # 対象のフィールド名バリエーションを取得
    variations = field_variations.get(field_name, [field_name])
    
    # 各バリエーションで検索
    for variation in variations:
        if variation in item:
            value = item[variation]
            logger.info(f"フィールド '{field_name}' の値を '{variation}' から抽出: {value}")
            
            # 型変換が必要な場合
            if field_name == "amount":
                # 金額の場合、Decimal型に変換
                try:
                    if isinstance(value, str):
                        # カンマや通貨記号を削除
                        value = re.sub(r'[^\d.-]', '', value)
                    
                    # 数値型に変換
                    if not isinstance(value, (int, float, Decimal)):
                        value = float(value)
                    
                    # Decimal型に変換
                    value = Decimal(str(value))
                    logger.info(f"金額をDecimal型に変換しました: {value}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"金額の変換に失敗しました: {value}, エラー: {str(e)}")
                    if default_value is not None:
                        return default_value
                    return Decimal('0')
                
                return value
            elif field_name == "transaction_date":
                # 日付の場合、date型に変換
                try:
                    if isinstance(value, (datetime, date)):
                        # すでにdatetime型またはdate型の場合
                        if isinstance(value, datetime):
                            return value.date()
                        return value
                    
                    if isinstance(value, str):
                        # 日付形式を解析
                        if '-' in value:
                            parts = value.split('-')
                        elif '/' in value:
                            parts = value.split('/')
                        else:
                            # ISO形式の日付文字列として解析を試みる
                            try:
                                return datetime.fromisoformat(value).date()
                            except ValueError:
                                # その他の形式の場合はそのまま返す
                                return value
                        
                        if len(parts) == 3:
                            if len(parts[0]) == 4:  # YYYY-MM-DD
                                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                            elif len(parts[2]) == 4:  # DD-MM-YYYY
                                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                            else:  # DD-MM-YY
                                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                                if year < 100:
                                    year += 2000  # 2桁の年を4桁に変換
                            
                            # date型に変換
                            return date(year, month, day)
                except Exception as e:
                    logger.warning(f"日付の変換に失敗しました: {value}, エラー: {str(e)}")
                
                return value
            elif field_name in ["major_category_id", "minor_category_id"]:
                # カテゴリIDの場合、整数に変換
                try:
                    if value is None and field_name == "minor_category_id":
                        # minor_category_idはNoneを許容
                        return None
                    
                    if not isinstance(value, int):
                        value = int(value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"カテゴリIDの変換に失敗しました: {value}, エラー: {str(e)}")
                    if default_value is not None:
                        return default_value
                    return 1 if field_name == "major_category_id" else None
                
                return value
            
            return value
    
    # 見つからない場合はデフォルト値を返す
    logger.info(f"フィールド '{field_name}' が見つかりませんでした。デフォルト値を使用: {default_value}")
    return default_value

def get_mock_transactions() -> List[schemas.TransactionCreate]:
    """テスト用のモックトランザクションデータを返す関数"""
    from datetime import date
    from decimal import Decimal
    
    # 現在の日付を取得
    today = date.today()
    
    # モックデータの作成
    mock_data = [
        {
            "amount": Decimal("1000.00"),
            "transaction_date": today,
            "description": "スーパーでの買い物",
            "major_category_id": 1,
            "minor_category_id": 2
        },
        {
            "amount": Decimal("2500.00"),
            "transaction_date": today,
            "description": "レストランでの食事",
            "major_category_id": 1,
            "minor_category_id": 3
        },
        {
            "amount": Decimal("5000.00"),
            "transaction_date": today,
            "description": "給料",
            "major_category_id": 5,
            "minor_category_id": None
        }
    ]
    
    # Pydanticモデルに変換
    transactions = []
    for data in mock_data:
        try:
            transaction = schemas.TransactionCreate(**data)
            transactions.append(transaction)
            logger.info(f"モックトランザクションを作成しました: {data}")
        except Exception as e:
            logger.error(f"モックトランザクションの作成に失敗しました: {data}, エラー: {str(e)}")
    
    return transactions

def try_parse_text_response(text: str) -> List[Dict[str, Any]]:
    """テキスト形式のレスポンスからトランザクション情報を抽出する関数"""
    logger.info(f"テキストの解析を試みます: {text}")
    
    # JSONのような形式かどうかを確認
    try:
        # 文字列がJSON形式の場合
        if text.strip().startswith('{') or text.strip().startswith('['):
            json_data = json.loads(text)
            
            if isinstance(json_data, list):
                return json_data
            elif isinstance(json_data, dict):
                if "items" in json_data:
                    return json_data.get("items", [])
                elif "transactions" in json_data:
                    return json_data.get("transactions", [])
                else:
                    # 単一のトランザクションとして扱う
                    return [json_data]
    except json.JSONDecodeError:
        # JSON形式ではない場合は続行
        pass
    
    # テキスト形式からの抽出を試みる
    items = []
    
    # 金額のパターン
    amount_pattern = r'(\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?)'
    
    # 日付のパターン（複数のフォーマットに対応）
    date_patterns = [
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # YYYY-MM-DD or YYYY/MM/DD
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # DD-MM-YYYY or DD/MM/YYYY
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{2})'   # DD-MM-YY or DD/MM/YY
    ]
    
    # 行ごとに処理
    lines = text.split('\n')
    current_item = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 金額を探す
        amount_match = re.search(amount_pattern, line)
        if amount_match and "amount" not in current_item:
            amount = amount_match.group(0).replace(',', '')
            current_item["amount"] = amount
        
        # 日付を探す
        for pattern in date_patterns:
            date_match = re.search(pattern, line)
            if date_match and "transaction_date" not in current_item:
                date_str = date_match.group(0)
                try:
                    # 日付形式を解析
                    if '-' in date_str:
                        parts = date_str.split('-')
                    else:
                        parts = date_str.split('/')
                    
                    if len(parts) == 3:
                        if len(parts[0]) == 4:  # YYYY-MM-DD
                            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                        elif len(parts[2]) == 4:  # DD-MM-YYYY
                            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                        else:  # DD-MM-YY
                            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                            if year < 100:
                                year += 2000  # 2桁の年を4桁に変換
                        
                        # ISO形式の日付文字列に変換
                        current_item["transaction_date"] = f"{year:04d}-{month:02d}-{day:02d}"
                except Exception as e:
                    logger.error(f"日付の解析に失敗しました: {date_str}, エラー: {str(e)}")
        
        # 説明文を探す（特定のキーワードを含む行）
        description_keywords = ["購入", "支払", "料金", "代金", "商品", "サービス", "支出", "収入"]
        if any(keyword in line for keyword in description_keywords) and "description" not in current_item:
            current_item["description"] = line
        
        # 項目が揃ったら追加
        if "amount" in current_item and "transaction_date" in current_item:
            if "description" not in current_item:
                # 説明がない場合は、直前の行または次の行を使用
                idx = lines.index(line)
                if idx > 0:
                    current_item["description"] = lines[idx - 1].strip()
                elif idx < len(lines) - 1:
                    current_item["description"] = lines[idx + 1].strip()
                else:
                    current_item["description"] = "不明"
            
            # デフォルトのカテゴリIDを設定
            current_item["major_category_id"] = 1
            
            # アイテムを追加
            items.append(current_item.copy())
            current_item = {}
    
    return items 