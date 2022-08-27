from typing import List

from . import buffer


def collection_read(filename):
    collections = {}
    with open(filename, "rb") as db:
        collections["version"] = buffer.read_uint(db)
        collections["num_collections"] = buffer.read_uint(db)
        collections["collections"] = []
        for i in range(collections["num_collections"]):
            collection = {"name": buffer.read_string(db), "size": buffer.read_uint(db), "hashes": []}
            for _ in range(collection["size"]):
                collection["hashes"].append(buffer.read_string(db))
            collections["collections"].append(collection)
    return collections


def collection_write_one(fn: str, name: str, hashes: List[str]):
    collection = collection_read(fn)

    buffer_data = buffer.WriteBuffer()
    buffer_data.clear_buffer()

    # 写入开头的版本号信息与收藏夹数量
    buffer_data.write_uint(collection['version'])
    buffer_data.write_uint(collection['num_collections'] + 1)

    # 循环写入之前的收藏夹
    for c in collection['collections']:
        buffer_data.write_string(c['name'])
        buffer_data.write_uint(c['size'])
        for h in c['hashes']:
            buffer_data.write_string(h)

    # 写入新的收藏夹
    buffer_data.write_string(name)
    buffer_data.write_uint(len(hashes))
    for h in hashes:
        buffer_data.write_string(h)

    with open(fn, "wb") as f:
        f.write(buffer_data.data)
