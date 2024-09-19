import json
from database import (
    get_latest_id_by_partition,
    check_field_exists,
    insert_entity,
    get_entity_by_field,
    update_entity_fields,
    get_all_entities,
)
from schemas import TABLE_NAMES, RefugeeTask


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
