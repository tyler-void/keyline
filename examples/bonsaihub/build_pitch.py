from keyline.pen import Deck

deck = Deck.from_brief("pitch.brief.toml")

# 01 cover
deck.next().text(
    "A dating app for bonsai trees and the people patient enough to keep them. "
    "Every match starts with a visit.",
    style="lede",
).note()

# 02 statement: the problem
deck.next().figure("median_tree_age").source()

# 03 evidence: a profile, from its front
deck.next(variant="figure").figure("profile_itoigawa_age").text(
    "Shimpaku juniper, collected from the wild.\n"
    "Looking for: someone who stays for decades.\n"
    "Dealbreakers: overwatering, wire left on past August.",
    region="side",
).source()

# 04 evidence: the four features
deck.next().table(
    [
        ["Feature", "What it does"],
        ["Swipe the front", "A tree from its front, with its age and care needs"],
        ["Slow Match", "A match unlocks after a full season of visits"],
        ["The Hub", "Close-ups of surface roots, bark and deadwood"],
        ["Wire Check", "A reminder to take wire off before it cuts"],
    ]
)

# 05 statement: the bet
deck.next().text(
    "Slow Match keeps anyone from adopting a juniper on impulse. The wait is the product.",
    style="lede",
)

# 06 evidence: what the wait buys
deck.next(variant="figure").figure("adoptions_reversed", accent=True).text(
    "Every keeper visits a tree for a season before adopting it. "
    "By then they know its front, its roots and its dealbreakers.",
    region="side",
).source()

# 07 evidence: keepers stay
deck.next(variant="figure").figure("retention_90d").text(
    "Ninety days is about one season. Keepers who wait for a tree stay with it.",
    region="side",
).source()

# 08 evidence: growth
deck.next().chart_bar("keepers_by_month", highlight="Sep").source()

# 09 evidence: supply is here
deck.next(variant="figure").figure("waitlist_trees").text(
    "The trees are already here. Growth now depends on keepers patient enough to visit them.",
    region="side",
).source()

# 10 evidence: revenue
deck.next(variant="figure").figure("premium_price").text(
    "Seasonal Boost is BonsaiHub's paid plan, billed by the month.",
    region="side",
).source()

# 11 close: the second visit
deck.next().text(
    "We are raising a $1.2M seed round. Next: Slow Match in Da Lat and Kyoto.",
    style="lede",
).source().note()

deck.save("pitch.pptx", author="Tyler")
