#!/usr/bin/env python3
"""Example for aiohttp.web basic server"""

import mdl
import asyncio
import os.path
import textwrap
import aiohttp

from aiohttp.web import run_app


class ItemID(object):

    def __init__(self, value):
        self.value = value


@mdl.format('itemID')
class ItemIDFormat(mdl.SwaggerFormat):

    def to_wire(self, item):
        return item.value

    def to_python(self, value):
        return ItemID(value)


##########################
# Simple handler
##########################
async def index(ctx):
    return textwrap.dedent(
        """
        Type {url}/hello/John  {url}/simple or {url}/{item_id}/ in browser url bar

        """).format(url='127.0.0.1:8080', item_id='12345')


################################
# Path parameter in swagger spec
################################
async def item_info(ctx):
    return "Body changed item_id: %s (%s)\n\n" % (
        ctx.params.item_id.value,
        type(ctx.params.item_id.value))


################################
# Streaming response
################################
def stream(stream):
    resp = yield from aiohttp.request(url='http://python.org', method='get')
    blob = yield from resp.read()
    yield from stream.write(blob)


async def prepare_stream(ctx):
    ctx.response.enable_chunked_encoding(256)
    return mdl.aiohttp.Stream(stream)


# init app
def init(loop):
    config = mdl.Configurator(mdl.aiohttp.Loader)
    config.load_mdl_file(
        os.path.join(os.path.dirname(__file__), 'aiohttp_web_srv.mdl'))
    reg = config.commit()
    reg.install()

    app = mdl.aiohttp.init_applications(reg, loop=loop)
    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = init(loop)
    run_app(app)
else:
    app = init(asyncio.get_event_loop())
