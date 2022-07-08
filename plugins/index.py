from datasette import hookimpl
from urllib.parse import quote

SEARCH_SQL = """
select
    pages.rowid,
    pages.*,
    documents.path,
    pages_fts.rank,
    pages.*,
    snippet(pages_fts, 0, '<b>', '</b>', '...', 160) as highlighted
from
    pages
    join pages_fts on pages.rowid = pages_fts.rowid
    join documents on pages.document_id = documents.id
where
    pages_fts match :q
order by
    pages_fts.rank, pages.rowid
""".strip()


@hookimpl
def extra_template_vars(request, template, datasette):
    async def inner():
        db = datasette.get_database()
        if template == "index.html":
            q = request.args.get("q", "").strip()
            next = request.args.get("next", "").strip()
            results = []
            count = 0
            next_token = None
            not_first_page = False
            if q:
                kwargs = {"q": q}
                if next and next.count(":") == 1:
                    not_first_page = True
                    search_sql = "with outer as ({}) select * from outer where (rank, rowid) > (cast(:rank as float), cast(:rowid as integer)) limit 21".format(
                        SEARCH_SQL
                    )
                    kwargs["rank"], kwargs["rowid"] = next.split(":")
                else:
                    search_sql = SEARCH_SQL + " limit 21"
                count_sql = "select count(*) from ({})".format(SEARCH_SQL)
                count = (await db.execute(count_sql, {"q": q})).single_value()
                results = [to_page(r) for r in (await db.execute(search_sql, kwargs))]
                if len(results) > 20:
                    results = results[:20]
                    next_token = "{}:{}".format(
                        results[-1]["rank"], results[-1]["rowid"]
                    )
            return {
                "q": q,
                "results": results,
                "count": count,
                "next_token": next_token,
                "not_first_page": not_first_page,
                "random_pages": [
                    to_page(r)
                    for r in (
                        await db.execute(
                            """
                            select pages.*, documents.path
                            from pages join documents on pages.document_id = documents.id
                            order by random() limit 6
                            """
                        )
                    )
                ],
            }
        return {}

    return inner


def to_page(r):
    return dict(
        r,
        filename=r["path"].split("/")[-1],
        imgix_url="https://sfms-history.imgix.net/{}".format(quote(r["path"])),
    )
