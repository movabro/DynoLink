import re
from datetime import datetime

class Transformer:
    def dynalist_to_notion_records(self, today_items, all_nodes):
        node_map = {node['id']: node for node in all_nodes}
        parent_map = self._build_parent_map(all_nodes)
        records = []
        for item in today_items:
            record = self._build_record(item, node_map, parent_map)
            records.append(record)
        return records

    def _build_parent_map(self, nodes):
        parent_map = {}
        for node in nodes:
            for child_id in node.get('children', []):
                parent_map[child_id] = node['id']
        return parent_map

    def _build_path(self, node_id, node_map, parent_map):
        path_nodes = []
        current_id = node_id
        while current_id and current_id in node_map:
            current_node = node_map[current_id]
            path_nodes.append(current_node)
            current_id = parent_map.get(current_id)
        return list(reversed(path_nodes))

    def _extract_tags(self, text):
        if not text:
            return []
        tags = re.findall(r"#([^\s#]+)", text)
        return [f"#{tag}" for tag in tags]

    def _format_path(self, path_nodes, path_tags):
        if path_tags:
            return " > ".join(path_tags)
        return " > ".join([node.get('content', '').strip() for node in path_nodes if node.get('content')])

    def _build_record(self, item, node_map, parent_map):
        path_nodes = self._build_path(item['id'], node_map, parent_map)
        path_tags = []
        for path_node in path_nodes:
            path_tags.extend(self._extract_tags(path_node.get('content', '')))

        if path_tags:
            top_tag = path_tags[0]
            sub_tags = path_tags[1:]
        else:
            item_tags = self._extract_tags(item.get('content', ''))
            top_tag = item_tags[0] if item_tags else ''
            sub_tags = item_tags[1:] if len(item_tags) > 1 else []

        created_timestamp = item.get('created', 0) / 1000
        created = datetime.fromtimestamp(created_timestamp)
        date_str = created.date().isoformat()

        return {
            'title': item.get('content', '').strip() or '(No content)',
            'date': date_str,
            'top_tag': top_tag,
            'sub_tags': list(dict.fromkeys(sub_tags)),
            'hierarchy_path': self._format_path(path_nodes, path_tags),
            'memo': item.get('note', '').strip()
        }