from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import smtplib
import uuid

from fastapi import HTTPException
from database import (
    get_latest_id_by_partition,
    check_field_exists,
    insert_entity,
    get_entity_by_field,
    update_entity_fields,
    get_all_entities,
)
from schemas import PARTITION_KEYS, TABLE_NAMES, RefugeeTask, WithdrawRequest


def process_task_resources(resources):
    if isinstance(resources, str):
        if resources.startswith("[") and resources.endswith("]"):
            try:
                return json.loads(resources)
            except json.JSONDecodeError:
                return [resources]
        else:
            return [resources]
    elif isinstance(resources, list):
        return resources
    elif resources is None:
        return []
    else:
        return list(resources)


# 写入难民用户表
def save_refugee_to_database(refugee: RefugeeTask) -> RefugeeTask:
    # 将难民数据插入到Refugee表中
    entity = {
        "PartitionKey": str(refugee.user_id),
        "RowKey": str(refugee.user_id),
        "user_id": refugee.user_id,
        "username": refugee.username,
        "phone": refugee.phone,
        "email": refugee.email,
        "password": refugee.password,
        "status": refugee.status.value,
        "created_at": refugee.created_at.isoformat(),
        "updated_at": refugee.updated_at.isoformat(),
    }
    insert_entity(TABLE_NAMES.REFUGEE, entity)
    return refugee


def save_withdraw_request(withdraw_request: WithdrawRequest) -> WithdrawRequest:
    # 将提现请求保存到数据库
    entity = {
        "PartitionKey": str(TABLE_NAMES.WITHDRAW_REQUEST),
        "RowKey": str(uuid.uuid4()),
        "user_id": withdraw_request.user_id,
        "amount": withdraw_request.amount,
        "payment_method": withdraw_request.payment_method,
        "request_date": withdraw_request.request_date.isoformat(),
        "status": withdraw_request.status.value,
        "created_at": withdraw_request.created_at.isoformat(),
        "updated_at": withdraw_request.updated_at.isoformat(),
    }

    # Try to insert the entity
    insert_entity(TABLE_NAMES.WITHDRAW_REQUEST, entity)
    return entity


def get_user_balance(user_id: str) -> float:
    # 从数据库获取用户余额
    user_entity = get_entity_by_field(
        TABLE_NAMES.REFUGEE, PARTITION_KEYS.PARKEY, user_id
    )
    if not user_entity:
        raise ValueError("User not found")
    return float(user_entity.get("balance", 0))


# 发送email方法
def send_email(to_email: str, subject: str, body: str):
    # Email configuration
    smtp_server = "smtp.example.com"  # Replace with your SMTP server
    smtp_port = 587  # Replace with your SMTP port
    smtp_username = "your_username"  # Replace with your SMTP username
    smtp_password = "your_password"  # Replace with your SMTP password
    from_email = "noreply@yourcompany.com"  # Replace with your sender email

    # Create message
    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    try:
        # Create SMTP session
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Enable TLS
            server.login(smtp_username, smtp_password)

            # Send email
            server.send_message(message)

        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise
