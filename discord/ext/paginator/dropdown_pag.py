from __future__ import annotations
from discord.ext.commands import Context
from discord import Interaction, SelectOption
from discord.ui import Select

from .paginator import Paginator, DefaultView

from typing import List, Optional, Union


class GenPlaceholder(object):
    """ Class used for generating placeholders dynamically between pages,

    .. rubric:: Example

    .. code-block:: py

        from discord.ext.paginator import GenPlaceholder

        class MyPlaceholder(GenPlaceholder):
            def generate(self, paginator):
                return 'Menu Page {current_page} out of {max_page}'.format(
                    current_page=paginator.current_page + 1,
                    max_page=paginator.max_page + 1
                )
    """
    def generate(self, paginator: DropdownPaginator) -> str:
        return 'Page {current} out of {max}'.format(
            current=paginator.current_page + 1, 
            max=paginator.max_page + 1)


class DropdownPaginatorView(DefaultView):
    _paginator: DropdownPaginator

    def _add_select(self) -> Select:
        class PagSelect(Select):
            def __init__(_, placeholder: str):
                super().__init__(placeholder=placeholder, options=self._options)
        
            async def callback(select_self, interaction: Interaction):
                value = select_self.values[0]
                page = await self._paginator.traverse_to(int(value))

                self._add_select()
                page['view'] = self
                if self._paginator.edit:
                    return await interaction.response.edit_message(**page)
                return await interaction.response.send_message(**page)
        
        if self._select:
            self.remove_item(self._select)

        if isinstance(self._paginator._placeholder, GenPlaceholder):
            placeholder = self._paginator._placeholder.generate(self)
        else:
            placeholder = self._paginator._placeholder
        self._select = PagSelect(placeholder)

        super().add_item(self._select)

    def __init__(self, ctx: Context, paginator: DropdownPaginator, *, timeout: Optional[float] = 180):
        super().__init__(ctx, paginator, timeout=timeout)

        self._options: List[SelectOption] = []
        self._select: Select = None

        for page, title in enumerate(self._paginator._titles):
            if isinstance(title, str):
                option = SelectOption(label=title, value=str(page))
            elif isinstance(title, dict):
                option = SelectOption(**title)
            else:
                raise TypeError(f'Invalid select option for "{title}", value must be str or dict, instead got {title.__class__.__name__}')
            self._options.append(option)
        self._add_select()

    

class DropdownPaginator(Paginator):
    """ Default implementation of a dropdown paginator

    .. note::

        All parameters from :class:`Paginator` are valid except ``view`` and ``allow_fast_traverse``  

    Parameters
    ----------
    placeholder: Union[:class:`str`, :class:`GenPlaceholder`]
        Placeholder to display,
        for dynamically generated placeholders use :class:`GenPlaceholder`
    """
    def __init__(self, *,
                 placeholer: Union[str, GenPlaceholder] = GenPlaceholder(),
                 **paginator_kwds) -> None:
        pages = paginator_kwds.pop('pages', [])
        self._titles = []
        self._placeholder = placeholer
        
        r = []
        for title, page in pages:
            self._titles.append(title)
            r.append(page)

        paginator_kwds['pages'] = r
        paginator_kwds['allow_fast_traverse'] = True
        paginator_kwds['view'] = DropdownPaginatorView

        super().__init__(**paginator_kwds)
