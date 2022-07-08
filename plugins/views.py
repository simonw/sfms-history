from datasette import hookimpl, Response
from urllib.parse import quote


@hookimpl
def register_routes():
    return [
        (r"^/docs$", docs),
        (r"^/docs/(?P<document_id>[a-z0-9]+)$", document),
        (r"^/docs/(?P<document_id>[a-z0-9]+)/(?P<page>\d+)/?$", page),
    ]


async def docs(datasette, request):
    db = datasette.get_database("sfms")
    documents = [
        to_document(doc)
        for doc in await db.execute(
            """
    select documents.*, count(*) as num_pages
    from pages join documents on pages.document_id = documents.id
    group by documents.id
    order by path
    """
        )
    ]
    return Response.html(
        await datasette.render_template("docs.html", {"documents": documents}, request)
    )


async def document(datasette, request):
    document_id = request.url_vars["document_id"]
    db = datasette.get_database("sfms")
    document = (
        await db.execute("select * from documents where id = ?", (document_id,))
    ).first()
    return Response.html(
        await datasette.render_template(
            "document.html",
            {
                "document": to_document(document),
                "pages": [
                    to_page(r)
                    for r in await db.execute(
                        "select pages.*, documents.path from pages join documents on pages.document_id = documents.id where document_id = ?",
                        (document_id,),
                    )
                ],
            },
            request,
        )
    )


async def page(datasette, request):
    document_id = request.url_vars["document_id"]
    page = request.url_vars["page"]
    db = datasette.get_database("sfms")
    document = (
        await db.execute("select * from documents where id = ?", (document_id,))
    ).first()
    page = (
        await db.execute(
            """
            select pages.*, documents.path
            from pages join documents on pages.document_id = documents.id
            where document_id = ? and page = ?""",
            (document_id, page),
        )
    ).first()
    return Response.html(
        await datasette.render_template(
            "page.html",
            {
                "document": to_document(document),
                "page": to_page(page),
            },
            request,
        )
    )


def to_page(r):
    return dict(
        r,
        filename=r["path"].split("/")[-1],
        imgix_url="https://sfms-history.imgix.net/{}".format(quote(r["path"])),
    )


def to_document(r):
    bits = r["path"].split("/")
    return dict(r, folder="/{}/".format("/".join(bits[:-1])).replace("//", "/"))
