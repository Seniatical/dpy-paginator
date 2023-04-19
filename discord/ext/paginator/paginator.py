# Base class for defining paginators
from __future__ import annotations
from discord.ext.commands import Context
from discord.ui import View
from discord import Embed, Interaction

from typing import Any, List, Dict, Callable, Type, Union, Optional


class PaginatorView(View):
    _paginator: Paginator

    async def on_timeout(self) -> None:
        await self._paginator.on_end()
        self.stop()

        return await super().on_timeout()


class DefaultView(PaginatorView):
    def __init__(self, ctx: Context, paginator: Paginator, *, timeout: Optional[float] = 180):
        self._ctx = ctx
        self._paginator = paginator

        super().__init__(timeout=timeout)


class Paginator(object):
    """ Base class for defining paginators

    Parameters
    ----------
    view: Type[:class:`ModifiedView`]
        View instance which handles editing messages,
        for built-in paginators such as :class:`ButtonsPaginator`,
        this arg is invalid.
    pages: List[Dict[:class:`str`, Any]]
        An array of pages, i.e messages to send as page.
        
        .. note::

            **This MUST be a dictionary**

            .. code-block:: diff
            
                  # Page content is sent using kwargs
                  # Where page = pages[page_index]
                + Context.send(**page)
    embeds: List[Union[:class:`Embed`, List[:class:`Embed`]]]
        An array of embeds or a 2d array of embeds to send as pages,
        if pages are provided then these are appended to these values.
    messages: List[:class:`str`]
        An array of message contents to send as pages,
        if pages are provided this overwrite previous content
    cyclical: :class:`bool`
        Whether you can traverse from start to end and vise versa once limit reached,
        if not end/start page are continually returned
    allow_fast_traverse: :class:`bool`
        Whether to allow direct traversing from start to end and vise versa
    current_page: :class:`int`
        Index of page paginator starts on, uses zero indexing
    start_page: :class:`int`
        Index of starting page for paginator, to use this value instead of current page,
        set current page to an invalid value e.g. ``-1``.
        This is also used when traversing to start directly.
    timeout: :class:`int`
        Timeout for paginator view, defaults to ``180``
    author_only: :class:`bool`
        Whether only the person who invoked the pagination is only allowed to respond
    edit: :class:`bool`
        Whether to edit existing view message or generate a new one.
    """
    ctx: Union[Context, Interaction]

    def __init__(
        self, view: Type[DefaultView], *,
        pages: List[Dict[str, Any]] = [],
        embeds: List[Union[Embed, List[Embed]]] = [],
        messages: List[str] = [],
        cyclical: bool = True,
        allow_fast_traverse: bool = False,
        ## original_message: Message = None,
        current_page: int = 0,
        start_page: int = 0,
        timeout: Optional[int] = 180,
        author_only: bool = True,
        edit: bool = True,
    ) -> None:
        if not issubclass(view, PaginatorView):
            raise ValueError('Invalid view class provided')

        self.view_cls = view
        self.allow_fast_traverse = allow_fast_traverse
        ## self.original_message = original_message
        self.pages = pages
        self.current_page = current_page
        self.start_page = start_page
        self.cyclical = cyclical
        self.ctx = None
        self.timeout = timeout
        self.author_only = author_only
        self.edit = edit

        self._can_traverse = True

        for i, v in embeds:
            if i > (len(self.pages) - 1):
                if not isinstance(v, list):
                    self.pages.append({'embeds': [v]})
                else:
                    self.pages.append({'embeds': v})
            else:
                c = self.pages[i].pop('embed', None)
                if isinstance(v, list):
                    v.append(c)
                else:
                    v = [c, v]
                if embeds := self.pages.get('embeds', []):
                    embeds.extend(v)
                    self.pages[i]['embeds'] = embeds
                else:
                    self.pages['embeds'] = v

        for i, v in messages:
            if i > (len(self.pages) - 1):
                self.pages.append({'content': v})
            else:
                self.pages[i]['content'] = v

        self.max_page = len(self.pages) - 1
        if self.current_page < 0 or self.current_page > self.max_page:
            self.current_page = self.start_page

    async def on_traverse_forward(self):
        """ An event called right before forward traversed page is returned """

    async def on_traverse_back(self):
        """ An event called right before backward traversed page is returned """

    async def on_traverse_start(self):
        """ An event called right before moving to Paginator.start_page """

    async def on_traverse_end(self):
        """ An event called right before moving to Paginator.max_page """

    async def on_traverse_to(self):
        """ An event called before a page is traversed to using :meth:`Paginator.traverse_to` """

    async def on_start(self):
        """ An event called when pagination starts, directly before message is sent """

    async def on_end(self):
        """ An event called when pagination ends, directly before message is sent """

    async def traverse_forward(self) -> Dict[str, Any]:
        """ Moves forward, i.e. next page """
        if not self._can_traverse:
            raise ValueError('Pagination ended')

        if (self.current_page >= self.max_page and not self.cyclical):
            return self.pages[self.current_page]
        elif self.current_page >= self.max_page:
            self.current_page = 0
        else:
            self.current_page += 1

        await self.on_traverse_forward()
        return self.pages[self.current_page]

    async def traverse_back(self) -> Dict[str, Any]:
        """ Moves backward, i.e previous page """
        if not self._can_traverse:
            raise ValueError('Pagination ended')

        if (self.current_page <= 0 and not self.cyclical):
            return self.pages[self.current_page]
        elif self.current_page <= 0:
            self.current_page = self.max_page
        else:
            self.current_page -= 1
        
        await self.on_traverse_back()
        return self.pages[self.current_page]

    async def traverse_start(self) -> Dict[str, Any]:
        """ Moves to the start, Paginator.start_page """
        if not self._can_traverse:
            raise ValueError('Pagination ended')
        if not self.allow_fast_traverse:
            return self.pages[self.current_page]
        self.current_page = self.start_page

        await self.on_traverse_start()
        return self.pages[self.current_page]

    async def traverse_end(self) -> Dict[str, Any]:
        """ Moves to the end, Paginator.max_page """
        if not self._can_traverse:
            raise ValueError('Pagination ended')
        if not self.allow_fast_traverse:
            return self.pages[self.current_page]
        self.current_page = self.max_page

        await self.on_traverse_end()
        return self.pages[self.current_page]

    async def traverse_to(self, page: int) -> Dict[str, Any]:
        """ Moves to a specific page

        Parameters
        ----------
        page: :class:`int`
            Page to traverse to
        """
        if not self._can_traverse:
            raise ValueError('Pagination ended')
        if not self.allow_fast_traverse:
            return self.pages[self.current_page]
        if page < 0 or page > self.max_page:
            return self.pages[self.current_page]
        self.current_page = page

        await self.on_traverse_to()
        return self.pages[self.current_page]

    async def end(self) -> None:
        """ Ends pagination """
        if not self._can_traverse:
            raise ValueError('Pagination already ended')
        self._can_traverse = False

        await self.on_end()
        self.ctx = None

    async def start(self, ctx: Union[Context, Interaction], *, timeout: int = ..., call: Callable[..., Any] = None) -> None:
        """Starts pagination

        Parameters
        ----------
        ctx: :class:`Context`
            Context to pass to view
        timeout: Optional[:class:`int`]
            Default timeout
        call: Callable[..., Any]
            Function to call rather then :meth:`ctx.send`

            .. admonition:: Example

                .. code-block:: py

                    await Paginator.context_start(Context, call=Context.reply)
        """
        assert issubclass(self.view_cls, DefaultView), 'Invalid view cls provided for context_start'

        self._can_traverse = True
        self.ctx = ctx
        if isinstance(ctx, Context):
            func = call or ctx.send
        else:
            func = call or ctx.response.send_message

        view = self.view_cls(ctx, self, timeout=timeout if timeout != ... else self.timeout)
        page = self.pages[self.current_page]
        page['view'] = view

        await self.on_start()
        await func(**page)
