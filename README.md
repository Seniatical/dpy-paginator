# Paginator
A pagination library for discord.py,
comes with support for dropdown, button based pagination

## Button Pagination
```py
from discord.ext.paginator import ButtonPaginator

pages = [
    {'content': 'Page 1'},
    {'content': 'Page 2'},
    {'content': 'Page 3'}
]
paginator = ButtonPaginator(pages=pages)

## In commands
await paginator.start(ctx=...)
```

## Dropdown Pagination
```py
from discord.ext.paginator import DropdownPaginator

pages = [
    ('Page 1', {'content': 'Page 1'}),
    ('Page 2', {'content': 'Page 2'}),
    ('Page 3', {'content': 'Page 3'})
]
paginator = DropdownPaginator(pages=pages)

## In commands
await paginator.start(ctx=...)
```
