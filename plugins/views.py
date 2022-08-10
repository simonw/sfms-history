from datasette import hookimpl, Response
from urllib.parse import quote, unquote_plus


@hookimpl
def register_routes():
    return [
        (r"^/docs$", docs),
        (r"^/docs/(?P<document_id>[a-z0-9]+)$", document),
        (r"^/docs/(?P<document_id>[a-z0-9]+)/(?P<page>\d+)/?$", page),
        (r"^/folders/(?P<folder>.*)$", folder),
    ]


async def folder(datasette, request):
    folder = unquote_plus(request.url_vars["folder"])
    db = datasette.get_database("sfms")
    documents = [
        to_document(doc)
        for doc in await db.execute(
            """
    select documents.*, count(*) as num_pages
    from pages join documents on pages.document_id = documents.id
    where path like ?
    group by documents.id
    order by path
    """,
            (folder + "/%",),
        )
    ]
    return Response.html(
        await datasette.render_template(
            "folder.html", {"documents": documents, "folder": folder}, request
        )
    )


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
                        """
                        select pages.*, documents.path
                        from pages join documents on pages.document_id = documents.id
                        where document_id = ?
                        order by page
                        """,
                        (document_id,),
                    )
                ],
            },
            request,
        )
    )


async def page(datasette, request):
    document_id = request.url_vars["document_id"]
    page_number = int(request.url_vars["page"])
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
            (document_id, page_number),
        )
    ).first()
    # Grab all other page numbers in this document
    page_numbers = [
        r["page"]
        for r in await db.execute(
            "select page from pages where document_id = ? order by page",
            (document_id,),
        )
    ]
    max_page = max(page_numbers)
    previous = None
    if page_number > 1:
        previous = page_number - 1
    next = None
    if page_number < max_page:
        next = page_number + 1
    return Response.html(
        await datasette.render_template(
            "page.html",
            {
                "document": to_document(document),
                "page": to_page(page),
                "page_numbers": page_numbers,
                "previous": previous,
                "next": next,
            },
            request,
        )
    )


def to_page(r):
    return dict(
        r,
        filename=r["path"].split("/")[-1],
        folder=r["path"].rsplit("/", 1)[0],
        folder_quoted=quote(r["path"].rsplit("/", 1)[0]),
        imgix_url="https://sfms-history.imgix.net/{}".format(quote(r["path"])),
    )


def to_document(r):
    bits = r["path"].split("/")
    return dict(r, folder="/{}/".format("/".join(bits[:-1])).replace("//", "/"))
