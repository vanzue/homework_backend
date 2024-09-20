from azure.data.tables import TableServiceClient, TableClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from typing import Dict, Any, List, Optional, Tuple
import logging
import configparser
import os

# 配置日志记录
# Azure SDK 日志级别包括：
# CRITICAL: 严重错误，可能导致程序终止
# ERROR: 错误，但不会导致程序终止
# WARNING: 警告信息，表示可能出现的问题
# INFO: 一般信息，用于跟踪程序的执行
# DEBUG: 调试信息，用于开发和故障排除

# 这里设置 Azure SDK 的日志级别为 WARNING
# 这意味着只会记录 WARNING、ERROR 和 CRITICAL 级别的日志
# 而 INFO 和 DEBUG 级别的日志将被忽略
logging.getLogger("azure").setLevel(logging.WARNING)


class AzureTableStorage:
    def __init__(self):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), "config.ini")
        config.read(config_path)
        self.connection_string = config["AzureStorage"]["connection_string"]
        self.table_service_client = TableServiceClient.from_connection_string(
            self.connection_string
        )

    def create_table(self, table_name: str) -> None:
        try:
            self.table_service_client.create_table(table_name)
            print(f"Table '{table_name}' created successfully.")
        except ResourceExistsError:
            print(f"Table '{table_name}' already exists.")

    def delete_table(self, table_name: str) -> None:
        try:
            self.table_service_client.delete_table(table_name)
            print(f"Table '{table_name}' deleted successfully.")
        except ResourceNotFoundError:
            print(f"Table '{table_name}' not found.")

    def insert_entity(
        self, table_name: str, entity: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        table_client = self.table_service_client.get_table_client(table_name)
        try:
            created_entity = table_client.create_entity(entity)
            print(f"Entity inserted successfully into table '{table_name}'.")
            # 获取新添加的数据
            partition_key = entity.get("PartitionKey")
            row_key = entity.get("RowKey")
            if partition_key and row_key:
                new_entity = table_client.get_entity(partition_key, row_key)
                return dict(new_entity)
            else:
                return dict(created_entity)
        except Exception as e:
            print(f"Error inserting entity into table '{table_name}': {str(e)}")
            return None

    def update_entity(self, table_name: str, entity: Dict[str, Any]) -> None:
        table_client = self.table_service_client.get_table_client(table_name)
        try:
            table_client.update_entity(mode="merge", entity=entity)
            print(f"Entity updated successfully in table '{table_name}'.")
        except Exception as e:
            print(f"Error updating entity in table '{table_name}': {str(e)}")

    def delete_entity(self, table_name: str, partition_key: str, row_key: str) -> None:
        table_client = self.table_service_client.get_table_client(table_name)
        try:
            table_client.delete_entity(partition_key, row_key)
            print(f"Entity deleted successfully from table '{table_name}'.")
        except ResourceNotFoundError:
            print(f"Entity not found in table '{table_name}'.")

    def query_entities(
        self, table_name: str, filter_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        table_client = self.table_service_client.get_table_client(table_name)
        try:
            entities = table_client.query_entities(filter_query)
            return [dict(entity) for entity in entities]
        except Exception as e:
            print(f"Error querying entities from table '{table_name}': {str(e)}")
            return []

    def get_latest_id_by_partition(self, table_name: str, partition_key: str) -> int:
        table_client = self.table_service_client.get_table_client(table_name)
        try:
            entities = table_client.query_entities("")
            entities_list = list(entities)

            if entities_list:
                # 找出最大的user_id
                max_user_id = max(
                    int(entity[partition_key]) for entity in entities_list
                )
                latest_id = max_user_id + 1
                return latest_id
            else:
                return 1
        except Exception as e:
            return 1

    def check_field_exists(
        self, table_name: str, field_name: str, field_value: Any
    ) -> bool:
        table_client = self.table_service_client.get_table_client(table_name)
        try:
            # 构建查询过滤器
            filter_query = f"{field_name} eq '{field_value}'"

            # 执行查询
            entities = table_client.query_entities(filter_query)

            # 检查是否有匹配的实体
            return any(entities)
        except Exception as e:
            print(f"Error checking field existence in table '{table_name}': {str(e)}")
            return False

    def get_entity_by_field(
        self, table_name: str, field_name: str, field_value: Any
    ) -> Optional[Dict[str, Any]]:
        table_client = self.table_service_client.get_table_client(table_name)
        try:
            # 构建查询过滤器
            if isinstance(field_value, (int, float)):
                filter_query = f"{field_name} eq {field_value}"
            else:
                filter_query = f"{field_name} eq '{field_value}'"

            # 执行查询
            entities = table_client.query_entities(filter_query)

            # 获取第一个匹配的实体
            entity = next(entities, None)

            if entity:
                return dict(entity)
            else:
                return None
        except Exception as e:
            print(f"Error getting entity by field from table '{table_name}': {str(e)}")
            return None

    def update_entity_fields(
        self,
        table_name: str,
        partition_key: str,
        row_key: str,
        fields_to_update: Dict[str, Any],
    ) -> bool:
        table_client = self.table_service_client.get_table_client(table_name)
        try:
            # 获取实体
            entity = table_client.get_entity(
                partition_key=partition_key, row_key=row_key
            )

            # 更新指定的多个字段
            for field_name, new_value in fields_to_update.items():
                entity[field_name] = new_value

            # 更新实体
            table_client.update_entity(entity=entity)

            return True
        except Exception as e:
            print(f"Error updating entity fields in table '{table_name}': {str(e)}")
            return False

    def get_all_entities(
        self, table_name: str, page: int = 1, page_size: int = 10, **search_params
    ) -> Tuple[List[Dict[str, Any]], int]:
        table_client = self.table_service_client.get_table_client(table_name)
        try:
            # 构建查询过滤器
            filter_query = []
            for key, value in search_params.items():
                if value is not None:
                    if isinstance(value, str):
                        # Try to convert string to int if it represents a number
                        try:
                            int_value = int(value)
                            filter_query.append(f"{key} eq {int_value}")
                        except ValueError:
                            filter_query.append(f"{key} eq '{value}'")
                    elif isinstance(value, (int, float)):
                        filter_query.append(f"{key} eq {value}")
                    elif isinstance(value, bool):
                        filter_query.append(f"{key} eq {str(value).lower()}")

            filter_string = " and ".join(filter_query) if filter_query else None
            print(filter_string)
            # 获取符合条件的实体
            if filter_string:
                entities = list(table_client.query_entities(filter_string))
            else:
                entities = list(table_client.list_entities())

            # 计算总数
            total_count = len(entities)

            # 计算分页
            start_index = (page - 1) * page_size
            end_index = start_index + page_size

            # 获取当前页的实体
            paginated_entities = entities[start_index:end_index]

            # 将实体转换为字典
            result = [dict(entity) for entity in paginated_entities]

            return result, total_count
        except Exception as e:
            print(f"Error getting entities from table '{table_name}': {str(e)}")
            return [], 0


# Example of how to call get_all_entities method

# 创建一个AzureTableStorage实例
azure_storage = AzureTableStorage()

# 导出方法供其他文件使用
create_table = azure_storage.create_table
delete_table = azure_storage.delete_table
insert_entity = azure_storage.insert_entity
update_entity = azure_storage.update_entity
delete_entity = azure_storage.delete_entity
query_entities = azure_storage.query_entities
get_latest_id_by_partition = azure_storage.get_latest_id_by_partition
check_field_exists = azure_storage.check_field_exists
get_entity_by_field = azure_storage.get_entity_by_field
update_entity_fields = azure_storage.update_entity_fields
get_all_entities = azure_storage.get_all_entities
