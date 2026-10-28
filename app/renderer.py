
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import ReportingAnalysis, COLLECTIONS, object_id
from .validation import snapshot, IntegrityError

ENV = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(["html"]),
)



def render(
    a: ReportingAnalysis,
    warnings=None,
    relation_reviews: RelationReviewResult | None = None,
) -> str:
    if warnings is None:
        warnings = []

    reviews = (
        relation_reviews.reviews
        if relation_reviews is not None
        else []
    )

    html = ENV.get_template("report.html.j2").render(
        a=a,
        collections=COLLECTIONS,
        object_id=object_id,
        warnings=warnings,
        relation_reviews=reviews,
    )


    for collection, ids in snapshot(a).items():
        if html.count(f'data-collection="{collection}"') != len(ids):
            raise IntegrityError(
                f"renderer component count mismatch: {collection}"
            )

        for item_id in ids:
            if html.count(f'data-object-id="{item_id}"') != 1:
                raise IntegrityError(
                    f"renderer ID preservation mismatch: {item_id}"
                )

    return html

from .relation_review import RelationReviewResult
