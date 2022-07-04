from datasette import hookimpl

SEARCH_SQL = """
select
    pages.rowid,
    pages_fts.rank,
    pages.*,
    snippet(pages_fts, 0, '<b>', '</b>', '...', 160) as highlighted
from
    pages
    join pages_fts on pages.rowid = pages_fts.rowid
where
    pages_fts match :q
order by
    pages_fts.rank, pages.rowid
""".strip()

@hookimpl
def extra_template_vars(request, template, datasette):
    async def inner():
        db = datasette.get_database()
        if template == "pages/page/{rowid}.html":
            rowid = request.path.split("/")[-1]
            page = (await db.execute('select * from pages where rowid = ?', (rowid,))).first()
            return {
                "page": page,
            }
        if template == "index.html":
            q = request.args.get("q", "").strip()
            results = []
            count = 0
            if q:
                search_sql = SEARCH_SQL + " limit 20"
                count_sql = "select count(*) from ({})".format(SEARCH_SQL)
                count = (await db.execute(count_sql, {"q": q})).single_value()
                results = [dict(r) for r in (await db.execute(search_sql, {"q": q}))]
            return {
                "q": q,
                "results": results,
                "count": count,
            }
        return {}
    return inner
