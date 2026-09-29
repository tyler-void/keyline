"""The pen (spec 002 §6): the only supported way for the skill to put content on a slide.

    from keyline.pen import Deck

`Deck.from_brief(path)` or `Deck(pack=…, mode=…, voice=…, evidence=…)`, then one builder
per slide (`deck.next()` or `deck.add(role, headline)`), whose verbs fill named regions
with pack tokens, then `deck.save(path)`. No python-pptx type goes in or comes out
(D-015): every python-pptx call lives in `_writer_pptx`.
"""

from keyline.pen._api import Deck, SlideBuilder
from keyline.pen._errors import DoesNotFit, EvidenceError, PenError

__all__ = ["Deck", "DoesNotFit", "EvidenceError", "PenError", "SlideBuilder"]
