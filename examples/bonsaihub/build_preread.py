from keyline.pen import Deck

deck = Deck.from_brief("preread.brief.toml")

# 01 cover
deck.next().text(
    "A pre-read for the Q4 planning meeting. It asks for one decision: launch Slow Match "
    "in Da Lat and Kyoto before we build any new feature, and give it a season to work.",
    style="lede",
).note()

# 02 statement: the proposal
deck.next().text(
    "Three reasons, one on each of the next three pages: adoptions made slowly last; "
    "active keepers grow every month, faster each time; and trees are waiting for "
    "keepers, not for features.",
    style="lede",
)

# 03 evidence: slow adoptions last
deck.next(variant="figure").figure("adoptions_reversed", accent=True).text(
    "71% of keepers are still active after 90 days, about one season.\n"
    "Slow Match puts a season of visits before every match, so a keeper adopts a tree "
    "they already know.\n"
    "These numbers show that slow adoptions last. They do not yet prove that Slow Match "
    "is the cause: we have no comparison without it.",
    region="side",
).source()

# 04 evidence: growth
deck.next(variant="figure").chart_bar("keepers_by_month", highlight="Sep").text(
    "Each month from April to September added more keepers than the month before.\n"
    "The pilots test whether the same curve starts again in a new city.",
    region="side",
).source()

# 05 evidence: keepers are the constraint
deck.next(variant="figure").figure("waitlist_trees").text(
    "We have 3,180 active keepers: almost four waiting trees for each one.\n"
    "A new feature gives today's keepers more to do. A new city brings new keepers, "
    "and keepers are what the waitlist needs.",
    region="side",
).source()

# 06 evidence: the features we have
deck.next().table(
    [
        ["Feature", "What it does", "September signal"],
        ["Swipe the front", "Shows a tree from its front, with its age and care needs", "3.2% of swipes go right"],
        ["Slow Match", "Unlocks a match only after a season of visits", "0.4% of adoptions reversed"],
        ["The Hub", "A feed of close-ups of roots, bark and deadwood", "No number yet"],
        ["Wire Check", "Reminds keepers to take wire off before it cuts the bark", "1,900 wire scars prevented"],
    ]
).source()

# 07 close: a season before a new feature
deck.next().text(
    "Approve it at the Q4 meeting, and Slow Match spends this quarter in Da Lat and Kyoto. "
    "New features wait until both cities are live.",
    style="lede",
)

deck.save("preread.pptx", author="Tyler")
