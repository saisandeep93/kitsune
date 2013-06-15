from django.core.management.base import BaseCommand

from kitsune.wiki.models import Document
from kitsune.wiki.tfidf import TFIDFAnalysis, find_word_locations_en_like
from kitsune.wiki.config import CATEGORIES

class Command(BaseCommand):
    def handle(self, *arg, **kwargs):
        docs = Document.objects.filter(locale='en-US', is_archived=False,
                                       is_template=False,
                                       category__in=(CATEGORIES[0][0], CATEGORIES[1][0]))

        analysis = TFIDFAnalysis()

        for doc in docs:
            if doc.redirect_url():
                continue

            if not doc.current_revision or not doc.current_revision.summary:
                continue

            analysis.feed(doc.id, [(doc.title, 1.2), (doc.current_revision.summary, 1)], find_word_locations_en_like)
        analysis.done = True

        # top search are "cookies", "private browsing", "update", "clear cache"
        # update is currently problematic

        if len(arg) == 0:
            import json, sys
            oi = analysis.offline_index()
            g = json.dumps(oi)
            print >> sys.stderr, len(oi)
            print >> sys.stderr, len(g)
            print g
        else:
            if arg[0] == "search":
                oi = analysis.offline_index()
                potential_docs = {}
                for term in arg[1:]:
                    docs = oi.get(term, [])
                    for doc_id, score in docs:
                        s = potential_docs.setdefault(doc_id, 0)
                        s += score
                        potential_docs[doc_id] = s

                for doc_id, score in reversed(sorted(potential_docs.items(), key=lambda x: x[1])):
                    doc = Document.objects.get(id=doc_id)
                    print doc, score
            else:
                for a in analysis.tfidf_doc(arg[0]):
                    print a
