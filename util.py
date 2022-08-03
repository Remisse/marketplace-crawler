def difference(list1: list, list2: list):
    return [x for x in list1 if x not in list2]

def trim(lst: list, max_size: int):
    if len(lst) > max_size:
        return lst[int(max_size / 2):]
    return lst

def tag_coalesce(x, default):
    return x.text if x is not None else default

def truncate(string: str, length: int) -> str:
    return string[:length] + "..." if len(string) > length else string