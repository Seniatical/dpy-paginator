from __future__ import annotations
from discord.ext.commands import Context
from discord.ui import Button, Item
from discord import ButtonStyle, Interaction

from .paginator import Paginator, DefaultView

from typing import List, Optional, Union
from copy import deepcopy


TRAVERSE_START      = "⏪"
TRAVERSE_BACK       = "◀️"
TRAVERSE_STOP       = "⏹️"
TRAVERSE_FORWARD    = "▶️"
TRAVERSE_END        = "⏩"

DEFAULT_START       = Button(style=ButtonStyle.primary, emoji=TRAVERSE_START, row=1)
DEFAULT_BACK        = Button(style=ButtonStyle.primary, emoji=TRAVERSE_BACK, row=1)
DEFAULT_STOP        = Button(style=ButtonStyle.primary, emoji=TRAVERSE_STOP, row=1)
DEFAULT_FORWARD     = Button(style=ButtonStyle.primary, emoji=TRAVERSE_FORWARD, row=1)
DEFAULT_END         = Button(style=ButtonStyle.primary, emoji=TRAVERSE_END, row=1)


class ButtonPaginatorView(DefaultView):
    _paginator: ButtonPaginator

    _start = None
    _end = None

    def _add_items(self):
        if self._paginator.allow_fast_traverse:
            _start = deepcopy(self._paginator._start)
            _start.callback = self.get_traverse_start()
            self.add_item(_start)
            self._start = _start

        _back = deepcopy(self._paginator._back)
        _back.callback = self.get_traverse_back()
        self.add_item(_back)

        _stop = deepcopy(self._paginator._stop)
        _stop.callback = self.get_traverse_stop()
        self.add_item(_stop)

        _forward = deepcopy(self._paginator._forward)
        _forward.callback = self.get_traverse_forward()
        self.add_item(_forward)

        if self._paginator.allow_fast_traverse:
            _end = deepcopy(self._paginator._end)
            _end.callback = self.get_traverse_end()
            self.add_item(_end)
            self._end = _end

        self._back = _back
        self._stop = _stop
        self._forward = _forward
        self._extras = []

    def _update_extras(self):
        if self._paginator._per_page:
            try:
                items = self._paginator.extras[self._paginator.current_page]

                if items == [-1]:
                    return
            except IndexError:
                return
            else:
                for i in self._extras:
                    self.remove_item(i)
                self._extras.clear()

                for item in items:
                    self.add_item(item)
                    self._extras.append(item)
        else:
            for i in self._extras:
                self.remove_item(i)
            self._extras.clear()

            for item in self._paginator.extras:
                self._extras.append(item)
                self.add_item(item)

    def __init__(self, ctx: Context, paginator: ButtonPaginator, *, timeout: Optional[float] = 180):
        super().__init__(ctx, paginator, timeout=timeout)
        self._add_items()
        self._update_extras()

    def get_traverse_start(self):
        async def traverse_start(interaction: Interaction):
            page = await self._paginator.traverse_start()
            page['view'] = self

            self._update_extras()
            if self._paginator.edit:
                return await interaction.response.edit_message(**page)
            return await interaction.response.send_message(**page)
        return traverse_start

    def get_traverse_end(self):
        async def traverse_end(interaction: Interaction):
            page = await self._paginator.traverse_end()
            page['view'] = self

            self._update_extras()
            if self._paginator.edit:
                return await interaction.response.edit_message(**page)
            return await interaction.response.send_message(**page)
        return traverse_end

    def get_traverse_back(self):
        async def traverse_back(interaction: Interaction):
            page = await self._paginator.traverse_back()
            page['view'] = self

            self._update_extras()
            if self._paginator.edit:
                return await interaction.response.edit_message(**page)
            return await interaction.response.send_message(**page)
        return traverse_back

    def get_traverse_stop(self):
        async def traverse_stop(interaction: Interaction):
            self.stop()
            self._paginator._can_traverse = False

            if self._paginator.allow_fast_traverse:
                self._start.disabled = True
                self._end.disabled = True
            self._back.disabled = True
            self._stop.disabled = True
            self._forward.disabled = True

            return await interaction.response.edit_message(view=self)
        return traverse_stop

    def get_traverse_forward(self):
        async def traverse_forward(interaction: Interaction):
            page = await self._paginator.traverse_forward()
            page['view'] = self

            self._update_extras()
            if self._paginator.edit:
                return await interaction.response.edit_message(**page)
            return await interaction.response.send_message(**page)
        return traverse_forward


class ButtonPaginator(Paginator):
    '''
    Default implementation for button pagination

    .. note::

        All parameters apart from ``view`` from :class:`Paginator` are valid.

    Parameters
    ----------
    traverse_start_button: ``Button``
        Custom start button, callback will be overwritten
    traverse_back_button: ``Button``
        Custom back button, callback will be overwritten
    traverse_stop_button: ``Button``
        Custom stop button, callback will be overwritten
    traverse_forward_button: ``Button``
        Custom forward button, callback will be overwritten
    traverse_end_button: ``Button``
        Custom end button, callback will be overwritten
    extras: List[Union[List[``Item``], ``Item``]]
        Extra components to add to paginator
    '''
    def __init__(self, *,
        traverse_start_button: Button = DEFAULT_START,
        traverse_back_button: Button = DEFAULT_BACK,
        traverse_stop_button: Button = DEFAULT_STOP,
        traverse_forward_button: Button = DEFAULT_FORWARD,
        traverse_end_button: Button = DEFAULT_END,
        extras: List[Union[List[Item], Item]] = [],
        **paginator_kwds
    ) -> None:
        paginator_kwds['view'] = ButtonPaginatorView

        super().__init__(**paginator_kwds)

        self.extras = extras

        if extras:
            if isinstance(extras[0], list):
                assert all(isinstance(i, list) for i in extras), 'Invalid extras provided'
                self._per_page = True
            else:
                assert all(isinstance(i, Item) for i in extras), 'Invalid extras provided'
                self._per_page = False

        self._start = traverse_start_button
        self._back = traverse_back_button
        self._stop = traverse_stop_button
        self._forward = traverse_forward_button
        self._end = traverse_end_button
