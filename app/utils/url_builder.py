from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote

def build_filter(filters: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not filters:
        return None
    frags = []
    op_map = {
        "eq": "eq", "ne": "ne", "gt": "gt", "lt": "lt",
        "ge": "ge", "le": "le", "like": "substringof",
        "in": "in",
    }
    for f in filters:
        field = f.get("field")
        op = op_map.get(f.get("op","eq"), "eq")
        value = f.get("value")
        if op == "like":
            # substringof('value', field)
            frags.append(f"substringof('{value}', {field})")
        elif op == "in" and isinstance(value, list):
            list_vals = ",".join([f"'{v}'" if isinstance(v,str) else str(v) for v in value])
            frags.append(f"{field} in ({list_vals})")
        else:
            v = f"'{value}'" if isinstance(value, str) else str(value)
            frags.append(f"{field} {op} {v}")
    return " and ".join(frags)

def build_get_url(base_url: str, base_path: str, entity: str, fields=None, filters=None, top=100, skip=0, orderby=None) -> str:
    entity_path = f"{base_path.rstrip('/')}/{entity}"
    params = {}
    if fields:
        params['$select'] = ",".join(fields)
    fil = build_filter(filters)
    if fil:
        params['$filter'] = fil
    if orderby:
        params['$orderby'] = orderby
    if top is not None:
        params['$top'] = str(top)
    if skip:
        params['$skip'] = str(skip)
    qs = urlencode(params, quote_via=quote, doseq=True)
    return f"{base_url.rstrip('/')}/{entity_path}?{qs}" if qs else f"{base_url.rstrip('/')}/{entity_path}"

def build_entity_key_segment(key_fields: Dict[str, Any]) -> str:
    parts = []
    for k,v in key_fields.items():
        parts.append(f"{k}='{v}'" if isinstance(v,str) else f"{k}={v}")
    return f"({','.join(parts)})" if parts else ""
