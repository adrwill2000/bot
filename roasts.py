"""
roasts.py — The soul of the bot. All roast content lives here.
Parody/comedy insults about bad trading calls. No actual malice intended.

THEME: Everything is a scam. The coin is a scam. The chart is a scam.
       The caller is either running a scam or falling for one. Always.

Roast count by category:
  CALL_ROASTS_GENERIC        — 120 lines
  CALL_ROASTS_SCAM_COIN      —  60 lines (coin-specific scam angle)
  CALL_ROASTS_NO_TARGET      —  40 lines
  CALL_ROASTS_NO_STOP        —  50 lines
  CALL_ROASTS_HIGH_ENTRY     —  35 lines
  CALL_ROASTS_MICRO_TARGET   —  30 lines
  CALL_ROASTS_BIG_TARGET     —  25 lines
  DUPLICATE_ROAST_TEMPLATES  —  40 templates
  PNL_WIN_ROASTS             —  60 lines
  PNL_LOSS_ROASTS            —  80 lines
  PNL_BREAK_EVEN_ROASTS      —  30 lines
  SPIKE_ROASTS               —  50 lines
  EXTRA_ROASTS               —  60 lines (inline button)
"""

import random
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# CALL ROASTS — GENERIC  (fires on every call)
# ─────────────────────────────────────────────────────────────────────────────

CALL_ROASTS_GENERIC = [
    # Scam-direct
    "Congratulations on participating in what appears to be a completely legitimate financial opportunity. 🚨",
    "This coin has more red flags than a communist parade. You called it anyway. Respect.",
    "Bold of you to call this. The whitepaper is three paragraphs and an AI-generated image of a dog.",
    "The team is anonymous. The roadmap is a meme. The tokenomics are a war crime. You called it. Iconic.",
    "The dev wallet holds 40% of supply. This is fine. Everything is fine. Call logged.",
    "According to the website, this project will 'revolutionize finance.' According to the chart, it will not.",
    "The auditors found seventeen critical vulnerabilities. The community called it a FUD attack. You called the coin. Here we are.",
    "Congrats on calling something that has definitely not already been rugged twice under a different name.",
    "This is either the next Bitcoin or the next exit scam. Market says the latter. You said the former. Fascinating.",
    "Launched by an anonymous team, no audit, CA renounced, and somehow you are bullish. Noted.",
    "The telegram admin just pinned 'NO THIS IS NOT A RUG' which is exactly what you say right before a rug.",
    "This coin's main utility is teaching people what a rug pull feels like. Educational content.",
    "Based on the tokenomics, this is essentially a structured way to give money to strangers on the internet.",
    "Someone gave this project a 1/10 on rug.watch. Someone else called it anyway. That someone is you.",
    "The liquidity is locked for 30 days. The dev's conviction lasted 29. You called it at day 28. Incredible timing.",
    "I've reviewed the contract. The only thing more concerning than the code is that you read it and still called this.",
    "A 500x on a coin with a $200k mcap requires a $100m buy. The math is not mathing. But the call is logged.",

    # TA-based mockery
    "Bold of you to enter a trade with such confidence and so little research.",
    "This call has the energy of someone who learned TA from a YouTube Short.",
    "Entry logged. Therapist notified.",
    "The chart looked at this entry and asked to remain anonymous.",
    "Buying here is certainly… a choice. A bold one. A wrong one, probably.",
    "Someone's definitely using astrology for their support levels.",
    "Ah yes, the classic 'buy high and pray' strategy.",
    "I've seen smarter financial decisions on a scratch card.",
    "Entry confirmed. Darwin Award application submitted.",
    "Your risk management called. It's filing a restraining order.",
    "This is either genius or a cry for help. I'm going with the latter.",
    "The market makers are literally pointing at you and laughing right now.",
    "Your portfolio is about to go on a spiritual journey.",
    "Fortune favours the bold. This is not bold. This is reckless.",
    "I consulted three indicators before writing this roast. You should've done the same before this call.",
    "Even the memecoin community thinks this needs more DD.",
    "Call locked in. God has been notified. He's busy. You're on your own.",
    "The support level you're trusting was drawn at 3am by someone who also bought LUNA.",
    "Sir, that's not a cup and handle. That's a cliff with a ledge.",
    "This candlestick pattern is called the 'Descending Financial Disaster.' It's in the textbooks now.",
    "The RSI is screaming. The MACD is crying. The Bollinger Bands have filed for witness protection.",
    "Triple bottom confirmed. The bottom was triple wrong.",
    "Drawn a trendline through three points that aren't even close to a line. Submitted a call anyway. Legendary.",
    "Your TA is technically correct in the same way that astrology is technically a belief system.",
    "The 200-day MA just crossed under the 50-day MA while the volume dried up. You: 'bullish.'",
    "Called the dip. It was not the dip. This is the new dip. You will call this one too.",
    "The chart is a staircase going down. You found the one step that went sideways and called it a reversal.",

    # Behaviour-based mockery
    "Sir/Ma'am, this is a Wendy's. But sure, go off.",
    "Buying here because the name sounds cool is still a strategy, technically.",
    "Call locked in. The influencer who shilled this has already sold.",
    "The Telegram group has 200k members, 199k of whom are bots. You are the 200,001st person to enter.",
    "Bought because someone on Twitter with 12 followers said 'LFG.' This is the origin story.",
    "The KOL who called this is getting paid in tokens that are now worth less than the tweet.",
    "You've entered a trade on a coin that was shilled in a Telegram group called 'GUARANTEED GAINS.' Peer reviewed.",
    "This call was definitely made with your own independent research and not because a YouTuber said 'not financial advice' five times.",
    "The influencer disclosed this as a paid promotion in font size 4 at the bottom of the post. You saw only the green candles.",
    "Someone paid a celebrity to tweet about this. The celebrity has no idea what blockchain is. Neither do they.",
    "DYOR was done. The research was: it went up yesterday. Entry submitted.",
    "Your thesis is 'vibes.' Historically, vibes have a 23% win rate. Call logged.",
    "Market cap: unknown. Use case: unclear. Team: anonymous. Conviction: maximum. Absolutely normal.",
    "The only utility this token has demonstrated is extracting money from optimistic strangers.",
    "This project has a Discord with 50,000 members and zero product. That is the product.",
    "The roadmap says 'Q1 2024: Moon.' It is now Q4. The moon remains unaffected. Call noted.",
    "Entered the trade because the chart 'looks like it wants to go up.' Vibes-based technical analysis. Accepted.",
    "You're now bag-holding the spiritual successor to four projects that all ended in the same way.",
    "The Twitter account for this project posts the same motivational crypto quotes every three days. This is their entire marketing budget.",
    "The last three people who called this never came back to post their PnL. You seem optimistic.",
    "A coin with this much hype and this little substance can only be described as a masterpiece of social engineering.",
    "The community calls critics 'paper hands.' The coin calls them 'people who kept their money.'",
    "This is FOMO in its purest, most crystalline form. A laboratory-grade specimen.",
    "You've entered a trade that 40,000 people entered simultaneously and called it 'early.'",
    "The dev just posted 'HUGE ANNOUNCEMENT SOON 🔥' for the eighth time this month. You are bullish. Interesting.",
]


# ─────────────────────────────────────────────────────────────────────────────
# CALL ROASTS — SCAM COIN ANGLE  (randomly blended in)
# ─────────────────────────────────────────────────────────────────────────────

CALL_ROASTS_SCAM_COIN = [
    "Calling #{coin} is a bold choice for someone who presumably owns a mirror.",
    "#{coin} has the tokenomics of a pyramid scheme and the roadmap of a fortune cookie. Bullish.",
    "#{coin}: where dreams go to become cautionary tales. Your call has been logged.",
    "If #{coin} were a restaurant, the health inspector would have condemned it three times by now.",
    "#{coin} is essentially a mechanism for redistributing wealth from optimists to anonymous wallets.",
    "The #{coin} whitepaper is 40 pages of words that individually make sense but collectively mean nothing.",
    "#{coin}'s only audited feature is its ability to drain liquidity at precisely the worst moment.",
    "Calling #{coin} with this kind of conviction is impressive. Impressively misplaced.",
    "#{coin} makes more sense as a case study in social engineering than as an investment.",
    "In five years, #{coin} will be mentioned in a documentary. The documentary will not be flattering.",
    "#{coin} is proof that the market will fund absolutely anything if the logo is good enough.",
    "The #{coin} team has delivered exactly what they promised: regular tweets and no product.",
    "#{coin} described itself as 'the future of finance.' So did the last seven projects that rugged.",
    "#{coin} has broken every ATH. Unfortunately those ATHs were -40%, -60%, and -80%.",
    "#{coin}: technically a token. Economically, a science experiment in how long hope can survive.",
    "The #{coin} chart is a work of abstract art. Specifically, a Rothko. Just red. All the way down.",
    "#{coin} is so far underwater the chart needs a pressure rating.",
    "Calling #{coin} long when the dev wallet is moving is the financial equivalent of running toward the alarm.",
    "#{coin} has the fundamentals of a Ponzi, the chart of a Ponzi, and the community of a Ponzi. But it's probably fine.",
    "If #{coin} were a film, the twist ending is that the protagonists lose all their money.",
    "The #{coin} smart contract has a function called 'emergencyWithdraw.' The emergency is ongoing.",
    "#{coin}'s last major update was changing the Twitter banner. Their GitHub has two commits.",
    "According to on-chain data, the top 5 wallets hold 72% of #{coin}. The top 1 is the deployer. Good luck.",
    "#{coin} is the financial equivalent of a timeshare presentation: compelling in the moment, catastrophic in hindsight.",
    "The #{coin} telegram admin just said 'this is not financial advice' which is only something you say right before financial advice.",
    "#{coin} has been 'about to break out' for eleven consecutive months. It is very patient.",
    "#{coin}'s price action looks like someone dropped a piano from a ten-story building.",
    "The #{coin} community refers to holders as 'believers.' That is not a word that instils confidence.",
    "#{coin} promises to be deflationary. It is definitely deflating something.",
    "The only thing #{coin} has successfully decentralised is the blame for its failure.",
    "#{coin} once had a partnership announcement that turned out to be a partnership with a company that doesn't exist.",
    "#{coin} has never met a support level it couldn't break through like tissue paper.",
    "The #{coin} chart is essentially a tutorial on gravity.",
    "#{coin}: entered the chat. Immediately became a liability.",
    "#{coin} has all the hallmarks of a legitimate project except for the legitimacy.",
    "Calling #{coin} is like betting on a horse that's technically still running but mostly falling.",
    "#{coin} was described as 'undervalued' when it was at $10. Also at $5. Also at $1. Also at $0.10.",
    "#{coin} holders prefer the term 'long-term investors' to 'people who forgot to sell.'",
    "The #{coin} roadmap hasn't been updated since 2022. The Twitter has. Today's post: 'SOON™'",
    "#{coin} is built on technology that is either revolutionary or completely made up. The whitepaper doesn't fully resolve this question.",
    "The #{coin} dev has changed their Twitter name seven times. The project has shipped nothing once.",
    "#{coin} listed on a DEX so obscure it's essentially anonymous. This is where your money will live now.",
    "The #{coin} price oracle has been manipulated before. The team called it a 'test of resilience.'",
    "#{coin}'s 'partnership with a major CEX' turned out to be a listing on an exchange nobody has heard of.",
    "Buying #{coin} because it 'has a lot of room to grow' is optimistic when that room is the floor.",
    "The #{coin} founder gave a TED Talk. It was not about #{coin}. It was about something unrelated. The connection was unclear.",
    "#{coin} is technically on the blockchain. That's where the positive attributes end.",
    "#{coin} reached an all-time high of $0.0001 and it's been a long way down since.",
    "Calling #{coin} is like walking past a crime scene and deciding to move in.",
    "The #{coin} team just held an AMA. The hard questions were deleted. You're still bullish. Incredible.",
    "#{coin}'s liquidity pool is roughly the GDP of a medium-sized village. You have entered this market.",
    "#{coin} has a Certik score of 42. You have a conviction score of 100. Only one of these numbers will be validated.",
    "The #{coin} utility token has one known utility: filling wallets temporarily before emptying them permanently.",
    "#{coin}: technically not a rug. Just every metric of a rug without the official title.",
    "The #{coin} chart's lower lows are getting lower. Eventually they become a philosophical question.",
    "#{coin} has more burn events than a bonfire festival. The only thing they haven't burned is the dev's wallet.",
]


# ─────────────────────────────────────────────────────────────────────────────
# CALL ROASTS — NO TARGET
# ─────────────────────────────────────────────────────────────────────────────

CALL_ROASTS_NO_TARGET = [
    "No target set — a true artist, painting chaos with no frame.",
    "No TP? Incredible. You plan to hold through the inevitable -80% with sheer will.",
    "No target because 'the vibes will tell me when to exit.' 🎱",
    "Missing target. Missing stop. Missing two brain cells. Impressive hat-trick.",
    "No target price. No exit plan. This is not investing. This is falling in love with a scam.",
    "Exit strategy: unknown. Outcome: predictable.",
    "Interesting choice to enter a scam token with no exit plan. Very zen. Very broke.",
    "The target is 'up.' The timeline is 'soon.' The outcome is 'we don't talk about it.'",
    "No target set. The plan is to hold forever or until the project rug-pulls, whichever comes first.",
    "Entered without a target. The market will set one for you. You won't like it.",
    "No TP means this position will live in your portfolio like a bad houseguest. Indefinitely.",
    "The target is 'when it moons.' The moon is approximately 384,000km away. Good luck.",
    "Having no target on a scam token is like getting in a car with no destination. You'll still end up somewhere. Just nowhere good.",
    "No take-profit set. This trade is going to die in a hospital bed with family gathered round.",
    "The absence of a target here suggests either extreme confidence or extreme avoidance. The market doesn't care which.",
    "No TP. This is either a diamond hands play or a hostage situation. The chart will decide.",
    "Entered without a target because 'it could go higher.' It could also go to zero. Both are technically true.",
    "No exit strategy on a coin that's essentially a countdown timer to a rug. Interesting.",
    "Not setting a target because 'you just feel it.' The market doesn't share your feelings.",
    "The target appears to be 'infinity.' The reality appears to be 'floor.'",
    "No TP set. The plan is vibes-based profit-taking, which historically has a 12% success rate.",
    "Running a trade with no target is like starting a sentence with—",
    "The bull case is written. The exit case is TBD. TBD usually means never.",
    "No target set on what is, architecturally speaking, a digital pyramid scheme. Fascinating approach.",
    "Entered without a take-profit because 'this one is different.' It is not different.",
    "No target. Just hope. Hope is not a strategy. It is, however, a feeling, and this trade has a lot of it.",
    "The trade has been entered. The target has not been thought about. This sequence of events is familiar.",
    "No TP because 'you're going to let it run.' Right into the dev wallet, probably.",
    "Setting no target on a zero-utility scam token is either bold or deeply spiritual.",
    "Target: unset. Cope: maximum. Timeline: undefined. Outcome: red.",
    "No target? No problem. The scam will set the exit for you.",
    "Not setting a TP is a choice that says 'I trust this project more than I trust myself.' That is concerning on multiple levels.",
    "Enter: done. Plan: vibes. Target: later. Result: you know what the result is going to be.",
    "Without a target, this trade is essentially a donation with extra steps.",
    "No take-profit. Just an open position bleeding into an anonymous wallet somewhere.",
    "The only thing more dangerous than trading a scam is trading a scam without an exit.",
    "No TP set. This is what financial archaeology will look like in five years.",
    "Entered without a target because the chart 'looks strong.' The chart looks like a controlled demolition.",
    "Not setting a target here is like going skydiving without planning when to pull the cord.",
    "The conviction is real. The target is theoretical. The rug is inevitable.",
]


# ─────────────────────────────────────────────────────────────────────────────
# CALL ROASTS — NO STOP LOSS
# ─────────────────────────────────────────────────────────────────────────────

CALL_ROASTS_NO_STOP = [
    "No stop loss. Classic. This isn't trading, it's a hostage situation.",
    "No stop loss set. This call and your account will be together until death do them part.",
    "Stop loss: none. Cope level: maximum. Courage: misplaced.",
    "The absence of a stop loss is doing a lot of heavy lifting here.",
    "No stop loss provided. The support is 'hopium and prayer.'",
    "No stop loss on a scam token. The bravery. The absolute bravery.",
    "Trading a rug-in-progress without a stop loss is a level of commitment that deserves documentation.",
    "No stop set. The only exit strategy is 'wait for it to come back.' It will not come back.",
    "Stopped out: impossible. Loss realised: inevitable. Stop loss: absent. Risk management: fled the building.",
    "No stop loss because 'the project is fundamentally strong.' The fundamental strength is in question.",
    "No stop because 'it's already at support.' It's about to learn what sub-support looks like.",
    "Trading without a stop loss on a coin that's been described as a scam by three separate analysts. Bold.",
    "The stop loss field was left blank, which is a financial statement in itself.",
    "Without a stop loss, this isn't a trade. It's a prayer.",
    "No stop set. The plan is to 'average down.' This plan has a well-documented failure rate.",
    "No stop loss. This will be fine. (It will not be fine.)",
    "Running without a stop on a token that launched four days ago is what they'll talk about at the funeral.",
    "Stop loss: TBD. Losses: pending. Regret: incoming.",
    "The absence of a stop loss suggests either supreme confidence or a complete misunderstanding of how scams work.",
    "No stop because 'strong hands.' Strong hands still have numbers on a screen. Those numbers can approach zero.",
    "No stop loss means you've made the market your stop loss. The market is not generous about this.",
    "Trading a low-liquidity scam with no downside protection is technically legal.",
    "No stop loss set. This is what a financial trust fall looks like.",
    "Without a stop loss, you've essentially given the market an open-ended invitation.",
    "No stop because the chart 'looks like it wants to hold here.' The chart has no wants. It has gravity.",
    "Running a naked long on a scam token with no stop is peak commitment.",
    "Stop loss: imaginary. Support level: fictional. Exit plan: undefined. Good luck.",
    "No stop loss. The risk/reward profile of this trade is best described as 'unhinged.'",
    "The only thing protecting this capital right now is optimism and a vague feeling.",
    "No stop set. This trade is held together with hopium and the goodwill of anonymous developers.",
    "Trading without a stop on a coin with a honeypot warning is a character study.",
    "No stop loss because 'crypto always recovers.' Not all crypto. Not this crypto.",
    "Stop loss absent. Maximum pain setting: enabled.",
    "Without a stop, this position will just keep existing until the project ceases to exist, which may happen first.",
    "No stop because 'it's a long-term hold.' Long-term holds still need risk management. Especially on scams.",
    "No stop loss provided. The market will provide one, on its own timeline, at its own price.",
    "Stop: not set. The project's honeypot contract will eventually set one for you.",
    "Trading a moonshot scam without a stop loss is one of the last truly free experiences left in finance.",
    "No stop loss. This trade and your capital will now begin an emotional journey together.",
    "No stop set on a coin the deployer wallet is still active on. Noted. Filed under 'brave.'",
    "Stop loss omitted. The chart will fill that role. The chart charges a premium.",
    "No stop because 'it can't go much lower.' Every coin that has ever gone to zero passed through this level.",
    "Running without a stop loss is the financial equivalent of driving at night with the headlights off.",
    "The stop loss was not set. The irony is that this coin was designed to make people feel exactly this way.",
    "No stop on a token where the deployer still holds 15% of supply. Outstanding risk management.",
    "Without a stop, the only question is whether you'll cut the loss or hold it into a support group.",
    "No stop because 'you believe in the project.' The project does not reciprocate this belief.",
    "Stop loss: absent. Faith: abundant. Capital: temporary.",
    "The stop loss section was deliberately ignored, which is a choice, and also a mistake.",
    "No stop on a scam. The scam will make its own exit. You might not get one.",
]


# ─────────────────────────────────────────────────────────────────────────────
# CALL ROASTS — HIGH ENTRY (chasing)
# ─────────────────────────────────────────────────────────────────────────────

CALL_ROASTS_HIGH_ENTRY = [
    "Buying at a local top. Bold. Tragic. Quintessentially human.",
    "Chasing price like a golden retriever chasing a car. Will also not know what to do if it catches it.",
    "FOMO has entered the chat and made a call.",
    "This entry price looks like you set a market buy at 3am after three energy drinks.",
    "Bought the local top of a scam. That's actually an achievement worth documenting.",
    "Entered right as the influencer who called this was selling. Classic.",
    "You've FOMO'd into a parabolic move on a coin that has no reason to exist. Respect.",
    "Chasing a pump on a scam token is the financial equivalent of running onto a departing train.",
    "This entry is so high the support levels are an entirely different chart.",
    "You've entered after a 300% pump on a coin with zero utility. This is art.",
    "Bought the very top of a scam pump. The people selling to you would like to thank you personally.",
    "This entry was timed exactly when the people who called it early were exiting. Poetic.",
    "Chasing a green candle on a rug-in-progress is a very specific kind of courage.",
    "Entering after a 10x is how you turn a scam's profit into your loss.",
    "The price went up because people were buying. It will go down for the same reason. You are now one of those people.",
    "FOMO-bought a token that peaked four hours ago. Technically you're a value investor now.",
    "The pump was orchestrated. You entered at peak orchestration. Outstanding timing.",
    "Entered at the exact price the dev team chose as their exit target. Congratulations on that coincidence.",
    "The chart went vertical. You entered vertical. Vertical things come down.",
    "Bought the parabolic extension of a coin described as a scam in its own contract comments.",
    "Entered at a price that implies a $50 billion market cap for something with no users, no product, and no audits.",
    "FOMO'd into a coin that had already 50x'd. The remaining 50x is theoretical. The reversal is not.",
    "The candle that brought you in is being described by analysts as a 'textbook distribution wick.'",
    "Buying here is technically buying after the people who started this project have already sold.",
    "You've entered after the pump. The dump is the natural sequel. The story arc is complete.",
    "The entry price assumes this token will be worth more than half the S&P 500. The math requires scrutiny.",
    "Bought at the local top of what is, by most definitions, a coordinated market manipulation event.",
    "FOMO is the most honest reason to enter a trade. It is also one of the worst.",
    "Entered during the pump's last gasp. The chart called this 'exit liquidity.' So did the deployers.",
    "Bought the blow-off top of a scam with no working product. This will be studied in classrooms.",
    "Entering after a vertical pump is like arriving at a party as everyone else is leaving. The Uber already came.",
    "This entry is so far above the 200MA that the 200MA sent a concerned letter.",
    "FOMO-entered a coin that had already rugpulled once, rebranded, and re-listed. The market's optimism is eternal.",
    "You've entered at maximum distribution, which means you're now the distribution.",
    "Chased the candle. The candle is now running in the other direction.",
]


# ─────────────────────────────────────────────────────────────────────────────
# CALL ROASTS — MICRO TARGET (tiny TP)
# ─────────────────────────────────────────────────────────────────────────────

CALL_ROASTS_MICRO_TARGET = [
    "That target is so low you could hit it with a mild cough.",
    "5% target? Risking your dignity for grocery money. Respect the hustle. No, actually, don't.",
    "Setting a 3% target with no stop loss is some kind of inverted risk/reward poetry.",
    "Risking it all for a 4% move on a scam token. The fees are going to take most of that anyway.",
    "A 2% target on a coin with 8% slippage. The math is not your friend here.",
    "Trading a volatile scam token for a 3% gain is like going fishing with a net full of holes.",
    "That target would make you about enough for a mediocre dinner. After fees, a bad coffee.",
    "Setting a 5% TP on a token that moves 40% in either direction is optimism at its most specific.",
    "Micro target on a maximum-risk asset. The risk/reward ratio is crying in a corner.",
    "A 3% target on something that can lose 90% overnight. This is the financial equivalent of dodging traffic to save 30 seconds.",
    "The target is set below the current bid-ask spread on some exchanges. Technically achievable. Practically a coin flip.",
    "Aiming for 4% on a coin where the dev wallet is one transaction from ending this trade entirely.",
    "Tiny TP on a scam. The house always wins by more than your target anyway.",
    "That target is so small the exchange fee will have a moment of recognition.",
    "5% target with infinite downside. The textbooks have a name for this. None of them are kind.",
    "The TP is essentially noise. The risk is existential. This ratio is not ideal.",
    "A 2% move on a scam token is the kind of precision that ignores everything else about the situation.",
    "Targeting 3% on something the deployer can tank 80% in a single transaction.",
    "This target suggests a careful, conservative approach to a coin that is architecturally reckless.",
    "A micro target on a macro-risk asset is technically a strategy. Just not a good one.",
    "That target represents the minimum plausible gain. The maximum possible loss is doing something very different.",
    "3% target on a 'community token' where the community is 90% bots. The maths don't love this.",
    "Targeting pocket change on something that could zero overnight. The optimism is almost admirable.",
    "A 5% TP on a honeypot-adjacent token. The sweet irony is that 5% might never be reachable.",
    "This target assumes the pump won't reverse before you can click sell. That's a lot to assume.",
    "Tiny target, maximum chaos. The definition of spending a dollar to win a dime.",
    "3% TP on a coin that is, conservatively speaking, a digital illusion.",
    "The fees, slippage, and spread have already eaten your target. The call is still logged though.",
    "Targeting a rounding error on a zero-utility token. There are bolder strategies.",
    "The target is achievable. The journey to get there on this particular coin is not.",
]


# ─────────────────────────────────────────────────────────────────────────────
# CALL ROASTS — BIG TARGET (unrealistic moonshot target)
# ─────────────────────────────────────────────────────────────────────────────

CALL_ROASTS_BIG_TARGET = [
    "That target would require this coin to surpass the GDP of Germany. The market cap math has been done.",
    "A 1000x target on a scam token with $50k liquidity. Beautiful. Completely delusional. Beautiful.",
    "Setting a 500% target assumes the project won't rug in the next 72 hours. That is a large assumption.",
    "The target is technically reachable if you believe in miracles, math errors, and anonymous developers.",
    "That target implies this coin will be worth more than Bitcoin. The coin launched last Thursday.",
    "A 10x target on something that went up 10x to reach this price. This is a 100x call in a costume.",
    "The target assumes perfect conditions: zero sells, locked liquidity, no devs, infinite buyers. Classic.",
    "Aiming for 1000% on a coin that is essentially a naming convention and a Telegram group.",
    "That target would make the market cap higher than Apple. For a dog coin. With no utility.",
    "The target is set at the number the KOL who shilled this said in their YouTube video. Noted.",
    "Targeting infinity on a scam is not a strategy. It is a feeling. Feelings close red.",
    "That TP is where the dev said the price is going. The dev is also the one selling to you.",
    "The target is a round number that was picked for emotional reasons, not analytical ones.",
    "Setting a 50x target on a coin with 12 holders is optimism that transcends the known universe.",
    "The target will require this scam to compete with projects that have actual engineers. Challenging.",
    "That target price requires a level of adoption that has never occurred for any coin, ever, in history.",
    "Aiming for a 500% gain on something that will lose 90% before it gains 10%. The sequence matters.",
    "The 100x target was set by the same person who told you this wasn't a scam. Take from that what you will.",
    "Targeting a 1000x on a memecoin with no utility, no team, and no product. The ambition is noted. The math is not.",
    "That price target assumes a market cap that would require sovereign wealth funds to buy a dog token. Interesting.",
    "The target is 'life-changing money.' The coin is trying to change something else about your life entirely.",
    "Setting a 50x TP on a honeypot. The irony is that the entry price is the only price that was ever achievable.",
    "That target was posted in the Telegram group by the person who deployed the contract. Draw your own conclusions.",
    "The moonshot target is filed. The actual shot will be horizontal and slightly downward.",
    "A 200x on a scam requires 200 times the number of people to be wrong after you. There's some precedent.",
]


# ─────────────────────────────────────────────────────────────────────────────
# DUPLICATE CALL ROASTS
# ─────────────────────────────────────────────────────────────────────────────

DUPLICATE_ROAST_TEMPLATES = [
    # Scam-specific
    (
        "🚨 {new} has confirmed what {orig} started: this scam now has TWO believers.\n"
        "{orig} entered at ${orig_price:,.4f}. {new} decided that wasn't enough victims and joined at ${new_price:,.4f}.\n"
        "The deployer thanks you both."
    ),
    (
        "📋 Two wallets. One scam. {orig} called #{coin} at ${orig_price:,.4f}.\n"
        "{new} reviewed this information and said 'yes, I also want some of that.'\n"
        "The anonymous dev team is having a very good day."
    ),
    (
        "🤝 {orig} and {new} have independently concluded that #{coin} is a good idea.\n"
        "Statistical modelling suggests that when two people agree a scam is legitimate, it is still a scam.\n"
        "{orig} at ${orig_price:,.4f}. {new} at ${new_price:,.4f}. The rug awaits them both."
    ),
    (
        "📡 DUPLICATE DETECTED. {new} is running on the same antenna as {orig}.\n"
        "The signal is #{coin}. The signal is wrong. ${orig_price:,.4f} met ${new_price:,.4f}.\n"
        "The dev wallet is currently reading both signals and smiling."
    ),
    (
        "🐑 {new} has followed {orig} into #{coin} like a sheep following another sheep into a wolf enclosure.\n"
        "Original entry: ${orig_price:,.4f}. Copycat entry: ${new_price:,.4f}.\n"
        "The wolf in this metaphor is an anonymous smart contract."
    ),
    (
        "🔁 History repeating. {orig} called #{coin} at ${orig_price:,.4f}.\n"
        "{new} witnessed this and thought 'I should also do this' at ${new_price:,.4f}.\n"
        "A support group has been formed. Attendance will likely be mandatory."
    ),
    (
        "💀 {new} has just duplicated {orig}'s #{coin} call.\n"
        "This is now a two-person operation walking into a scam with full confidence.\n"
        "${orig_price:,.4f} and ${new_price:,.4f} are now part of the same cautionary tale."
    ),
    (
        "🎭 {orig} opened the #{coin} scam play at ${orig_price:,.4f}.\n"
        "{new} entered stage left at ${new_price:,.4f}, unbothered by the critical reviews.\n"
        "Both performers will appear in the post-mortem discussion."
    ),
    (
        "🪞 {new} has looked at {orig}'s #{coin} call and said 'yes, this is exactly what I was about to do.'\n"
        "{orig}: ${orig_price:,.4f}. {new}: ${new_price:,.4f}.\n"
        "Mirror trading into a scam is technically a strategy. Just not a recommended one."
    ),
    (
        "🚂 {orig} boarded the #{coin} train at ${orig_price:,.4f}.\n"
        "{new} ran after it and jumped on at ${new_price:,.4f}.\n"
        "The train's destination is disclosed in the contract. Nobody read the contract."
    ),
    (
        "👯 TWINS! {new} and {orig} have arrived at the same #{coin} conclusion independently.\n"
        "{orig} at ${orig_price:,.4f}. {new} at ${new_price:,.4f}.\n"
        "When two people independently conclude a scam is legitimate, it is still a scam. But louder."
    ),
    (
        "📣 {orig} called #{coin} at ${orig_price:,.4f}. {new} heard this and doubled down at ${new_price:,.4f}.\n"
        "Between them, they have conducted zero audits, zero fundamental analysis, and infinite optimism.\n"
        "The dev wallet is the real winner here."
    ),
    (
        "🎰 {orig} placed their bet on #{coin} at ${orig_price:,.4f}.\n"
        "{new} saw the table and said 'deal me in' at ${new_price:,.4f}.\n"
        "The house is an anonymous Ethereum wallet. It always wins."
    ),
    (
        "🔬 Scientific finding: two separate market participants, given the same scam, will independently reach the same wrong conclusion.\n"
        "{orig} at ${orig_price:,.4f}. {new} at ${new_price:,.4f}. Sample size: adequate. Conclusion: known."
    ),
    (
        "📉 {new} has joined {orig} in the #{coin} recovery program, committing at ${new_price:,.4f}.\n"
        "{orig} got in at ${orig_price:,.4f}. They can compare notes later. The notes will be brief and red."
    ),
    (
        "🏗️ {orig} laid the foundation of this #{coin} mistake at ${orig_price:,.4f}.\n"
        "{new} added a second floor at ${new_price:,.4f}.\n"
        "Together they've built a structure on ground that is, architecturally, a scam."
    ),
    (
        "🌊 {orig} stepped off the #{coin} pier at ${orig_price:,.4f}.\n"
        "{new} watched and jumped in at ${new_price:,.4f}.\n"
        "Neither has checked how deep the water is. The deployer has drained the pool."
    ),
    (
        "🎓 {new} has submitted their #{coin} thesis alongside {orig}.\n"
        "{orig} opened at ${orig_price:,.4f}. {new} submitted at ${new_price:,.4f}.\n"
        "Both will be graded. The grade is already known. It is red."
    ),
    (
        "💌 {orig} sent a love letter to #{coin} at ${orig_price:,.4f}.\n"
        "{new} read it and decided to write one too at ${new_price:,.4f}.\n"
        "The recipient is an anonymous contract that does not reciprocate feelings."
    ),
    (
        "🎪 {orig} joined the #{coin} circus at ${orig_price:,.4f}. Welcome, {new}, at ${new_price:,.4f}.\n"
        "The clowns are the anonymous devs. You are the audience. This is not a compliment."
    ),
    (
        "⛽ {orig} fuelled the #{coin} pump at ${orig_price:,.4f}. {new} added more fuel at ${new_price:,.4f}.\n"
        "The fire they're feeding is warming someone else's anonymous wallet."
    ),
    (
        "🤡 {new} has confirmed the #{coin} thesis with {orig}.\n"
        "Two independent analysts. Same scam. ${orig_price:,.4f} meets ${new_price:,.4f}.\n"
        "The market is efficient. Just not in the direction you wanted."
    ),
    (
        "🎬 {orig} called 'action' on #{coin} at ${orig_price:,.4f}.\n"
        "{new} arrived on set at ${new_price:,.4f} without reading the script.\n"
        "The script is a rug pull. It was written before you both arrived."
    ),
    (
        "🧲 #{coin} has attracted two callers: {orig} at ${orig_price:,.4f} and {new} at ${new_price:,.4f}.\n"
        "What they're being attracted toward is a liquidity pool that's about to be drained."
    ),
    (
        "🔐 {orig} locked in #{coin} at ${orig_price:,.4f}. {new} locked in at ${new_price:,.4f}.\n"
        "The only thing actually locked here is their capital. The dev liquidity lock expires tomorrow."
    ),
    (
        "📻 {orig} broadcast #{coin} at ${orig_price:,.4f}. {new} received the signal loud and clear at ${new_price:,.4f}.\n"
        "The broadcast tower is a Telegram group. The signal is noise dressed as alpha."
    ),
    (
        "🌡️ {orig} diagnosed #{coin} as bullish at ${orig_price:,.4f}.\n"
        "{new} sought a second opinion at ${new_price:,.4f} and got the same wrong answer.\n"
        "The patient is not bullish. The patient is a scam."
    ),
    (
        "🎯 {orig} targeted #{coin} at ${orig_price:,.4f}. {new} acquired the same target at ${new_price:,.4f}.\n"
        "Two snipers. One scam. The scope was pointed at their own portfolios."
    ),
    (
        "🏋️ {orig} lifted #{coin} at ${orig_price:,.4f}. {new} spotted them at ${new_price:,.4f}.\n"
        "Nobody is spotting the exit. Nobody is reading the contract. This is fine."
    ),
    (
        "🗺️ {orig} mapped the #{coin} route at ${orig_price:,.4f}. {new} followed the map at ${new_price:,.4f}.\n"
        "The map was drawn by the deployer. It leads directly to their wallet."
    ),
    (
        "🧩 {orig} placed the first piece of the #{coin} puzzle at ${orig_price:,.4f}.\n"
        "{new} added the next piece at ${new_price:,.4f}.\n"
        "When the puzzle is complete, it spells 'EXIT SCAM.'"
    ),
    (
        "🏦 {orig} deposited faith into #{coin} at ${orig_price:,.4f}.\n"
        "{new} matched the deposit at ${new_price:,.4f}.\n"
        "The bank is unregistered and the CEO is anonymous. Standard stuff."
    ),
    (
        "🛸 {orig} and {new} have independently identified #{coin} as the next 1000x.\n"
        "${orig_price:,.4f} and ${new_price:,.4f}. Two believers. One digital illusion.\n"
        "The aliens who launched this are already gone."
    ),
    (
        "⚗️ {orig} conducted their #{coin} experiment at ${orig_price:,.4f}.\n"
        "{new} replicated the experiment at ${new_price:,.4f}.\n"
        "Science requires reproducibility. The result is reproducibly incorrect."
    ),
    (
        "🎸 {orig} played the opening chord of #{coin} at ${orig_price:,.4f}.\n"
        "{new} joined the band at ${new_price:,.4f}.\n"
        "The concert ends with the sound of a rug being pulled."
    ),
    (
        "🌋 {orig} walked toward the #{coin} volcano at ${orig_price:,.4f}.\n"
        "{new} saw this and thought 'I'll join' at ${new_price:,.4f}.\n"
        "The volcano is active. The lava is a sell order."
    ),
    (
        "🕳️ {orig} jumped into the #{coin} hole at ${orig_price:,.4f}.\n"
        "{new} jumped in after at ${new_price:,.4f}.\n"
        "The hole is the deployer's liquidity drain. It's deeper than either of them expects."
    ),
    (
        "📍 {orig} pinned #{coin} at ${orig_price:,.4f}. {new} pinned it too at ${new_price:,.4f}.\n"
        "Two pins in the same scam on the same map. The destination is the same for both."
    ),
    (
        "🧭 {orig} followed the #{coin} compass at ${orig_price:,.4f}. {new} followed at ${new_price:,.4f}.\n"
        "The compass is pointing toward the dev's exit. Both callers are now heading in the same direction."
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# PnL WIN ROASTS
# ─────────────────────────────────────────────────────────────────────────────

PNL_WIN_ROASTS = [
    "Stopped out in profit. The scam paid out this time. Buy a lottery ticket while you're hot.",
    "A win on a scam token. The universe is deeply inconsistent.",
    "Positive PnL. {name} will now be insufferable for exactly one week. Tick tock.",
    "It worked. Even a thrown dart hits the board eventually.",
    "Green exit. The lucky ones get out before the rug. {name} is, for now, lucky.",
    "The scam gave {name} money. This happens 30% of the time. The other 70% is where the cautionary tales live.",
    "A profit! Quick, screenshot before {name} redeploys this capital into something worse.",
    "Closed green on something that by all metrics should not have been green. The market is poetic sometimes.",
    "The exit was timed perfectly or accidentally. Either way, the PnL doesn't care.",
    "Won on a scam. The anonymous developers' loss distribution algorithm appears to have malfunctioned.",
    "{name} took profit from an entity specifically designed to extract profit from {name}. A comeback story.",
    "Positive outcome on a zero-utility token. There is no logical framework in which this was guaranteed.",
    "The exit was clean. The project will continue rugging people who hold longer than {name}.",
    "This win will be used as evidence in future bad trades. 'I've done it before' it will be said. Incorrectly.",
    "Closed at a profit. The narrative arc of this trade was better than most people's entire portfolio story.",
    "Green. {name} beat a scam. The scam has already found new victims. Everyone wins. Except the new victims.",
    "The trade worked out. Credit where it's due. Also please stop using this as a reason to YOLO more.",
    "A successful exit from a coin that is still descending toward zero. {name} ran faster than the rug.",
    "Profit confirmed. The anonymous team that built this is also, somewhere, confirming their own profits.",
    "Won the trade. Still called something that required a luck factor of approximately 8 out of 10.",
    "Closed in the green. Statistically this had to happen once. The law of large numbers is vindicated.",
    "Profit! Now the worst thing that can happen is {name} thinks this was skill.",
    "{name} successfully extracted value from a system that was designed to extract value from {name}. Impressive.",
    "The PnL is green. The project is still red. The difference is the exit timing and nothing else.",
    "A win! The charts rewarded {name}'s thesis. The thesis was still mostly wrong. The market didn't care.",
    "Positive close. The scam was patient with {name}. {name} was impatient with the scam. The impatience paid off.",
    "Green PnL on a coin that will rugpull the people who held longer. {name}'s exit is someone else's entry.",
    "Closed in profit. This outcome was not structurally guaranteed. {name} was lucky and should know this.",
    "The trade paid. The project is still a digital illusion. These two facts can coexist.",
    "Profit extracted from a scam. The economy of this is impressive. Don't try to repeat it systematically.",
    "A W! {name} should immediately resist the urge to size up on the next call.",
    "Won this one. The market giveth. It also taketh. Usually in that order, then the second one more.",
    "Closed green. The scam graduated one person to profit and dozens more to bag holding. {name} graduated.",
    "PnL: positive. Methodology: questionable. Result: undeniably real. Congrats, {name}.",
    "This trade went right. The key now is not interpreting 'went right' as 'was right all along.'",
    "Positive close. The project is still fundamentally a scam. The timing just happened to work for {name}.",
    "Got out in profit. This is the goal. Most people don't. {name} did. This conversation is over.",
    "Win logged. {name} beat the odds on a low-probability trade. The odds remain low for next time.",
    "The exit was perfect. The entry was questionable. The net result is green. That's the game.",
    "Profit. {name} is now statistically ahead of most people who ever bought this coin. That bar was low.",
    "Green exit. Somewhere, the deployer of this coin is mildly impressed by the timing.",
    "Called it and it worked. For the avoidance of doubt, the project is still a scam. Just a temporarily profitable one.",
    "Closed in the money. {name} should treat this as an exception, not a template.",
    "A profit was made. The coin continues its long journey toward a five-digit mcap.",
    "Win confirmed. Resist the urge to go larger on the next one. This is the important part.",
    "Green. Genuinely impressive given what was called. The market occasionally rewards the brave. Note: occasionally.",
    "Positive PnL on a coin that has the structural integrity of a wet napkin. A tribute to timing.",
    "Closed green. {name} is now statistically exempt from this wall of shame. For now.",
    "The trade resolved in {name}'s favour. The coin is still a scam. Nobody told the candles.",
    "Won. {name} will now refer to this as 'that time I called it perfectly' for the next 6 months.",
    "Exit in profit. Clean. Professional. Completely at odds with everything else about this token.",
    "Closed green on a coin that has no reason to be anything other than red. Justice is dead. PnL lives.",
    "The call was bold. The exit was clean. The profit is real. The coin is still a scam. All true simultaneously.",
    "A W on a scam. Somehow. The market has no morality and {name} just benefited from that.",
    "Green exit from a project that will eventually appear in a YouTube video titled 'I lost everything.'",
    "Profit! The anonymous devs are also in profit. Everyone is in profit at different times. This is how scams work.",
    "Closed in the green. {name} entered a burning building and came out holding something valuable. Incredible.",
    "The trade worked. The lesson shouldn't be 'this strategy works.' The lesson is 'this strategy worked once.'",
    "Positive close. {name} beat the house this round. The house has more rounds.",
    "Win! The chart cooperated. The project didn't deserve it. Neither did the entry. But the exit was clean.",
]


# ─────────────────────────────────────────────────────────────────────────────
# PnL LOSS ROASTS
# ─────────────────────────────────────────────────────────────────────────────

PNL_LOSS_ROASTS = [
    "And it's gone. As designed. This was the intended function of the coin.",
    "The scam scammed. This is what scams do. Welcome to the documentation.",
    "Negative PnL logged. The anonymous developers have received your contribution.",
    "The coin did what it was built to do. It's not broken. You were the mechanism.",
    "Closed at a loss on something that was described as a rug by three separate tools. Those tools were correct.",
    "The project's exit liquidity algorithm included {name}. It has been executed.",
    "A moment of silence for the capital that left for an anonymous wallet and is not returning.",
    "The rug arrived on schedule. {name} was present. The portfolio was adjusted accordingly.",
    "Stop losses exist. {name} chose vibes. Vibes have been updated to reflect current market conditions.",
    "The loss is logged. The lesson is free. The tuition was not.",
    "Closed red. The people who designed this outcome are pleased.",
    "This outcome was predicted by the contract, the tokenomics, the on-chain data, and three separate chat members. {name} remained optimistic.",
    "The scam ran its natural course. The ending was not a surprise to the people who designed it.",
    "At least they closed it. Some people are still holding. Those people have not yet met their loss.",
    "Red exit. The anonymous team has deployed their proceeds into their next project. This one is called something different.",
    "The trade closed in the direction the deployer intended it to. This is a design feature, not a bug.",
    "Negative PnL. {name} donated capital to a wallet address and received the experience in return.",
    "Loss confirmed. The market has graded this call. The grade is a number that starts with a minus.",
    "Closed at a loss. The first step to recovery is acknowledging the loss. The second is not calling the rebrand.",
    "The contract's 'tax on sell' is specifically designed to make this moment worse. It has succeeded.",
    "Red. {name}'s capital has been redistributed to a more anonymous location.",
    "This call closed exactly as the deployer planned from deployment day. {name} participated in someone else's thesis.",
    "The loss is real. The project is fake. The overlap between these two things is {name}'s portfolio.",
    "Negative PnL on a scam. The universe is functioning correctly.",
    "Loss logged. The only thing working as intended here is the scam itself.",
    "Closed red. The chart suggested this. The on-chain data suggested this. {name}'s conviction suggested otherwise. The chart was right.",
    "The liquidity was pulled. The price fell. The loss was incurred. The deployer's wallet grew. The cycle completes.",
    "Red exit. This was the planned outcome for everyone except {name}.",
    "Loss realised. The important word there is 'realised.' The next step is 'processed.'",
    "Closed in the red. Somewhere, the dev who built this is reading this message and nodding.",
    "The trade lost. The scam won. The scoreboard has been updated.",
    "Negative close. This is an expensive lesson in what 'anonymous team' means in practice.",
    "Loss locked in. The coin continues to search for lower lows. It will find them.",
    "Red. {name}'s belief in this project has been monetised by someone else.",
    "Closed at a loss. The only audit that matters was the deployer's audit of {name}'s entry price.",
    "The market answered the question of whether this was a scam. The answer cost money.",
    "Loss recorded. The coin's community will now say 'WAGMI' with slightly less conviction.",
    "Red exit from a project that was always going to produce red exits. This was the design.",
    "Closed red. The chart, the contract, the tokenomics, and common sense were all aligned on this one.",
    "Loss logged. The anonymous developer team has reached their fundraising target.",
    "This is the part of the story where {name} considers whether the person who called this was connected to the project.",
    "Negative PnL. The project has successfully executed its stated function, which was redistributing {name}'s capital.",
    "Loss confirmed. {name} entered a scam and the scam behaved like a scam. The math checks out.",
    "Closed in the red. The on-chain data was telling a very different story. Nobody read it. Except the dev.",
    "The trade lost. This is technically an educational outcome. The education was expensive.",
    "Red close on a coin that the deployer wallet was actively selling during. The signal was there.",
    "Negative PnL. The coin was described as a 'community-driven project' which means 'no team to hold accountable.'",
    "Loss locked in. The people who described this as a 'hidden gem' have found a different gem to describe.",
    "Closed red. The scam found an exit. The exit was {name}'s position.",
    "Loss confirmed. {name} trusted an anonymous team with real money. The anonymous team has moved on.",
    "Negative close. The project was always a fundraise for the deployer. The fundraise was successful.",
    "Red. The coin did exactly what the smart contract says it can do. {name} did not read the smart contract.",
    "Loss logged. The community will now gaslight anyone who called this a rug.",
    "Closed at a loss. The entire thesis was based on a Telegram message from someone with a cartoon avatar.",
    "The loss is now real. The project was always fake. The timeline was just delayed.",
    "Red exit. This was not bad luck. This was the project functioning exactly as designed.",
    "Negative PnL confirmed. {name}'s capital is now working for an anonymous party in an undisclosed location.",
    "Loss locked in. The exit liquidity this project needed was specifically {name}.",
    "Closed red. The scam scammed successfully. It usually does. That's why it's called a scam.",
    "Loss confirmed on a project that was listed on a spreadsheet of known scams. The spreadsheet was correct.",
    "Negative close. {name} invested in someone else's exit strategy. It has been exited.",
    "Red. The 'next big thing' has done the thing that the last five next big things also did.",
    "Loss logged. The coin is still going. Down. It has not stopped going down. This is the natural direction.",
    "Closed in the red on a token that had 'tax on sell' in the contract. The tax was collected.",
    "The trade went red. The deployer went green. This is the complete picture of what occurred.",
    "Negative PnL. The community called this 'market manipulation' and then went quiet.",
    "Loss confirmed. The only manipulation was in the promotional materials {name} used for their thesis.",
    "Red exit on a project that raised $2m and shipped nothing. The $2m was the product.",
    "Closed at a loss. The algorithm that produced this outcome is called 'a rug pull' and it worked perfectly.",
    "The call closed red. {name} will now undergo the traditional crypto grief cycle: denial, averaging down, acceptance.",
    "Loss logged. The coin has now fulfilled its designed purpose. The designer is no longer on Telegram.",
    "Negative close. This is not the market being irrational. This is the market being exactly rational about a scam.",
    "Red. The project tokenomics were described as 'innovative.' They were innovative in their ability to extract capital.",
    "Closed at a loss. The smart money was selling when the dumb money was buying. This is how it always goes.",
    "Loss confirmed. The project had 'strong fundamentals' in the sense that it fundamentally scammed people.",
    "Negative PnL. {name} provided exit liquidity to someone who understood the project better than they did.",
    "Red exit. The token is still listed. It's just worth significantly less than the entry price now.",
    "Loss locked in. The coin is not coming back. Neither is the capital. These are now historical facts.",
    "Closed red. The 'bullish catalyst' that justified this entry was a promotional tweet that has since been deleted.",
    "Negative close. {name} called a 'gem.' The gem was paste. The paste has been confirmed.",
]


# ─────────────────────────────────────────────────────────────────────────────
# PnL BREAK EVEN ROASTS
# ─────────────────────────────────────────────────────────────────────────────

PNL_BREAK_EVEN_ROASTS = [
    "Break-even. The scam respected {name} just enough to not actually scam them. Barely.",
    "Zero PnL. The only winner was the exchange, which took its fees and left.",
    "Flat exit. Not a loss, not a win — a philosophical statement about the nature of crypto.",
    "Broke even. The opportunity cost of this trade was tremendous and is not captured in the PnL.",
    "Break-even on a scam. This is the most expensive free trade {name} will ever make.",
    "Closed flat. {name} time-locked their capital in a scam and got it back. Minus fees. Barely.",
    "Zero net gain. The coin tried to scam {name} and came up slightly short. A moral victory for {name}.",
    "Flat close. The scam didn't quite get them. {name} didn't quite get the scam. Honours even.",
    "Break-even. The fees made this a loss in real terms. The optimism is not captured on the ledger.",
    "Closed at zero. This was a very dramatic way to end up where {name} started.",
    "Flat exit from a scam. The adrenaline cost more than the gain.",
    "Break-even. The scam was patient. {name} was more patient. The result was a draw.",
    "Zero PnL. The only thing that moved was {name}'s stress levels and the exchange's revenue.",
    "Flat close. {name} went toe-to-toe with a scam and both parties walked away. Respect.",
    "Break-even. Not the worst outcome for a coin that was designed to produce a much worse one.",
    "Closed at par. The scam failed to scam. {name} failed to profit. A rare deadlock.",
    "Zero PnL after fees means this trade was a net loss. The ledger is being optimistic.",
    "Flat exit. The emotional toll of this trade is not reflected in the zero-percent return.",
    "Broke even. This scam delivered the exact psychological experience of a loss with none of the catharsis.",
    "Closed at zero gain. The gas fees, the time, and the cortisol were not zero.",
    "Break-even on a token that should have produced a loss. The market had mercy. Once.",
    "Flat close. The scam blinked first. So did {name}. The result: absolutely nothing.",
    "Zero PnL. Technically not in the loss column. Technically in the 'nothing to show for it' column.",
    "Break-even close on a scam. The scam is still going. The next person to enter will not break even.",
    "Closed flat. {name} escaped with their capital and left the burn for the next buyer.",
    "Zero net. The chart went up, then down, ending exactly where it started. {name} rode the entire journey.",
    "Flat exit. This trade was a vivid, expensive, ultimately meaningless experience.",
    "Break-even on something that was a 50/50 between profit and full loss. The coin flip landed on neither.",
    "Closed at zero. The market made no judgment. The market is indifferent. This is almost worse than a loss.",
    "Flat PnL. The scam didn't execute. The trade didn't either. A very expensive standoff.",
]


# ─────────────────────────────────────────────────────────────────────────────
# SPIKE ALERT ROASTS
# ─────────────────────────────────────────────────────────────────────────────

SPIKE_ROASTS = [
    "Plot twist: {name} accidentally made money. The scam is malfunctioning.",
    "Nobody is more surprised than {name} right now. The deployer might be.",
    "Quick, {name}, take profits before the scam remembers what it's supposed to do.",
    "Broken clock, twice a day. Today is {name}'s day. The clock is still broken.",
    "The scam is pumping. {name} is, for now, a genius. This message has an expiry.",
    "UP {pct:.0f}%! The scam is in its honeymoon phase. The honeymoon ends.",
    "The chart mooned. Someone is distributing. That someone is not {name}.",
    "A {pct:.0f}% move. Either the fundamentals have changed or someone is coordinating a dump. Probably the second one.",
    "This spike is doing significant work to rehabilitate {name}'s reputation. Act accordingly.",
    "Apes together strong. {name} is presently very strong. The apes on the other side are also strong.",
    "The market giveth 50%. The market will taketh 70%. This is the way.",
    "Congrats on the spike. The people selling into this pump would like to thank {name} for the liquidity.",
    "UP {pct:.0f}%. This was not guaranteed. Take it. Do not wait for 200%. Take it now.",
    "The scam is pumping, which means someone orchestrated this and {name} is on the right side. Today.",
    "A spike! The deployer didn't rug today. They'll rug tomorrow. Today is a gift.",
    "Up {pct:.0f}% from call. The chart wants to go higher. The wallets selling into this want it to go lower.",
    "The scam is doing what scams do before they stop doing it. Act accordingly.",
    "{name}'s call is up {pct:.0f}%. The anonymous team is currently deciding when to end this.",
    "The pump is real. The project behind the pump is not. These facts are currently irrelevant.",
    "A {pct:.0f}% move on a scam is either a gift or a trap. Both lead to the same place eventually.",
    "Up massively. Take profits. The next roast for this coin will not be this celebratory.",
    "The coin spiked. {name} should close this before the deployer reads this message.",
    "{pct:.0f}% up. The people distributing at this price want {name} to feel FOMO and hold. Don't.",
    "Spike alert. The 'huge announcement' the devs promised is currently someone's exit liquidity.",
    "Up {pct:.0f}% and still a scam. A profitable scam for {name} if they exit before the plot twist.",
    "The price went up. {name} called it. Whether {name} called it for the right reasons is irrelevant.",
    "A {pct:.0f}% spike on a coin with no utility means someone printed more hope into the market. Harvest it.",
    "Spiking. The community is celebrating. The deployer is selling. These are different activities.",
    "Up {pct:.0f}%! The chart doesn't know this is a scam. The chart just moves. Right now it's moving right.",
    "{name}'s call is performing. The question is not whether it will reverse but when.",
    "The pump arrived. {name} is currently correct. Correctness has an expiry date on this one.",
    "Up {pct:.0f}% and climbing. The climbing will stop. Nobody will announce when. Take some off.",
    "Spike confirmed. The scam is rewarding early believers before switching strategies.",
    "{pct:.0f}% up. The natural next move is for the people who coordinated this to exit. Their next move is close.",
    "The chart is green and so is {name}'s PnL. This alignment is temporary on one of those fronts.",
    "A spike! The project is 'different.' The spike is not. Spikes reverse.",
    "Up {pct:.0f}% and the Telegram group is going insane. The devs are also going insane. To the bank.",
    "Congratulations on riding the pump. The dump is structurally required. Time is the only question.",
    "The call is working. {name} is right. For now, {name} is right. This sentence has a footnote.",
    "{name} called this before the pump. The pump arrived. The next call should be 'I'm taking profits.'",
    "Up {pct:.0f}%. The deployer's whitelist was not {name}'s wallet. The price action was for someone else first.",
    "The scam is performing as a pump-and-dump, not just a dump. {name} caught the pump half. Well timed.",
    "Spiked {pct:.0f}%. Take the win. The scam's next act does not involve green candles.",
    "A big move. {name}'s thesis is temporarily validated by price action and nothing else.",
    "Up {pct:.0f}% on a coin that has no reason to be up {pct:.0f}%. Markets are inefficient. {name} won this round.",
    "The spike is real. The project is not. Sell into the spike before the project catches up with reality.",
    "Up massively. {name}'s call is in profit. The window is open. Windows close.",
    "A {pct:.0f}% move has vindicated what is still, objectively, a scam. The vindication is temporary.",
    "{name} is right. Today. Take it.",
    "Spike! The scam is in its prime. Prime doesn't last long on these things.",
    "Up {pct:.0f}% and the community is calling {name} a visionary. {name} is a lucky person who should take profits.",
]


# ─────────────────────────────────────────────────────────────────────────────
# EXTRA ROASTS (inline 🔥 button)
# ─────────────────────────────────────────────────────────────────────────────

EXTRA_ROASTS = [
    "The chart doesn't care about your feelings. Neither does the deployer.",
    "I've seen more rigorous analysis from a Magic 8-Ball submerged in water.",
    "The only thing more volatile than this coin is the caller's risk management.",
    "TA stands for 'Tried Again.' At least the persistence is admirable.",
    "Somewhere, a financial advisor just got a chill down their spine and doesn't know why.",
    "The market makers saw this entry and updated their holiday bonus projections.",
    "Technical analysis was applied. It pointed at the exit. This was not the reading chosen.",
    "This trade has the structural integrity of a wet napkin.",
    "Conviction: high. Research: unknown. Outcome: being determined by an anonymous smart contract.",
    "We support all traders regardless of skill level. This call is testing the limits of that statement.",
    "The deployer of this coin is receiving push notifications about your position.",
    "This call is backed by the same analytical framework used to pick lottery numbers.",
    "The coin's smart contract has a function called 'killSwitch'. It has been used before.",
    "The influencer who shilled this received a bag of tokens as payment. Those tokens are being sold now.",
    "If this trade ends well, it will be due to luck and not the thesis.",
    "The whitepaper for this project is thirty pages of vision and zero pages of implementation.",
    "Three separate wallet trackers have flagged the deployer as a serial rugger. The call was made anyway.",
    "This is what 'going against the grain' looks like when the grain is also right.",
    "The coin's name was chosen for marketing purposes. The underlying utility was chosen for none.",
    "This trade's fundamental case rests entirely on something a person with 200 Twitter followers said.",
    "The chart's lower shadow on that last candle was a wick. Not a bounce. A wick.",
    "This is the financial equivalent of seeing a 'free money' sign and asking how many.",
    "The token has a 7% tax on buys and a 15% tax on sells. Your TP has been mathematically neutered.",
    "On-chain shows the top 10 wallets selling. The call was made anyway. The faith is noted.",
    "This project's main innovation is making the same scam look different enough to fool new people.",
    "The KOL who called this was paid in tokens and they are currently liquidating those tokens.",
    "Every support level on this chart has been support in the same way a wet floor is support: temporarily.",
    "The coin has had four 'massive partnerships' announced and zero products shipped. Solid foundations.",
    "The 'buy the dip' thesis requires this to be a dip and not a cliff. The data has opinions.",
    "Buying here because 'it can't go much lower' has historically been one of the most expensive sentences in crypto.",
    "This token's roadmap was last updated when a different coin was rugging. Priorities.",
    "The community mods delete any price discussion. This is a choice that communicates something specific.",
    "The deployer wallet moved 400k tokens to a new address two hours before this call. Good entry timing.",
    "Three accounts created in the same week are bullposting this coin. These are not organic holders.",
    "The contract has a 'blacklist' function. The deployer can turn off your ability to sell. This was not checked.",
    "The coin has 'anti-whale' measures unless you're the deployer, who holds 15%. Classic.",
    "This project was 'stealth launched,' which means the team bought everything before you got the chance.",
    "The 'partnership announcement' was a tweet from a project with 300 followers. The FOMO was real.",
    "Volume came from three wallets. Those wallets are rotating the supply. The entry was between rotations.",
    "This coin described itself as 'community owned' in the announcement and then a wallet sold 20% of supply.",
    "The project's Telegram has 80,000 members and posts nothing. This is a holding pen.",
    "There is a mint function in the contract. The deployer can print more tokens whenever they want.",
    "The 'huge catalyst' the community has been waiting on is a tweet from an account that follows three people.",
    "The audit was performed by a firm that has audited thirty rugs. All of which were 'safe' before rugging.",
    "Buy pressure is coming from one coordinated wallet. When that wallet stops, so does the price.",
    "This coin's volume to market cap ratio indicates wash trading. The wash is ongoing.",
    "The dev just 'burned' tokens. To their own wallet. This has been documented.",
    "The liquidity lock expires in six days. The deployment was three days ago. The math is uncomfortable.",
    "This project has rebranded twice. The original name was in the news for the wrong reasons.",
    "The honeypot scanner returned 'high risk.' The call was submitted. The scanner's feelings are hurt.",
    "The token deployer's other projects include three rugs, one slow bleed, and a rename. Call noted.",
    "Max wallet limits apply to everyone except the deployer, who holds 18% with no restriction.",
    "The 'organic growth' narrative requires ignoring that volume started sixty seconds after a coordinated signal.",
    "The project's website was registered yesterday. The whitepaper was generated by AI. The call was made today.",
    "This coin's community calls anyone who questions the project 'paper hands.' The paper hands were right.",
    "The 'dev doxxed' claim links to a LinkedIn with no connections and a headshot from a stock image site.",
    "The 'audit passed' badge was purchased. The contract still has six unresolved critical findings.",
    "This project's GitHub has two commits. One of them is the readme. The other is the readme again.",
    "The 'locked liquidity' is locked on a platform the deployer controls. This was not widely communicated.",
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_call_roast(name: str, coin: str, entry: float,
                   target: Optional[float], stop: Optional[float]) -> str:
    """
    Builds a multi-line roast combining:
    - One generic + possibly one scam-coin line
    - One target-specific line
    - One stop-specific line
    """
    lines = []

    # 70% chance of a scam-specific coin roast, 30% fully generic
    if random.random() < 0.70:
        scam_line = random.choice(CALL_ROASTS_SCAM_COIN).replace("#{coin}", f"#{coin}")
        generic_line = random.choice(CALL_ROASTS_GENERIC)
        # Alternate which comes first
        if random.random() < 0.5:
            lines.append(scam_line)
            lines.append(generic_line)
        else:
            lines.append(generic_line)
            lines.append(scam_line)
    else:
        lines.append(random.choice(CALL_ROASTS_GENERIC))
        lines.append(random.choice(CALL_ROASTS_GENERIC))

    # Target roast
    if not target:
        lines.append(random.choice(CALL_ROASTS_NO_TARGET))
    else:
        pct = (target - entry) / entry * 100
        if pct < 5:
            lines.append(random.choice(CALL_ROASTS_MICRO_TARGET))
        elif pct > 200:
            lines.append(random.choice(CALL_ROASTS_BIG_TARGET))

    # Stop roast
    if not stop:
        lines.append(random.choice(CALL_ROASTS_NO_STOP))

    # Remove any duplicate lines
    seen = set()
    unique = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)

    return "\n".join(unique)


def get_duplicate_roast(caller_name: str, original_name: str, coin: str,
                        original_price: float, new_price: float) -> str:
    template = random.choice(DUPLICATE_ROAST_TEMPLATES)
    return template.format(
        new=caller_name,
        orig=original_name,
        coin=coin,
        orig_price=original_price,
        new_price=new_price,
    )


def get_pnl_roast(name: str, coin: str, pnl_pct: float) -> str:
    if pnl_pct > 2:
        pool = PNL_WIN_ROASTS
    elif pnl_pct < -2:
        pool = PNL_LOSS_ROASTS
    else:
        pool = PNL_BREAK_EVEN_ROASTS
    return random.choice(pool).replace("{name}", name)


def get_spike_roast(name: str, coin: str, pct: float) -> str:
    return (random.choice(SPIKE_ROASTS)
            .replace("{name}", name)
            .replace("{pct:.0f}", str(round(pct)))
            .replace("{pct}", str(round(pct))))


def get_extra_roast() -> str:
    return random.choice(EXTRA_ROASTS)


# ─────────────────────────────────────────────────────────────────────────────
# LEADERBOARD TIER LABELS
# ─────────────────────────────────────────────────────────────────────────────

def get_trader_tier(avg_pnl: float, win_rate: float) -> str:
    if avg_pnl >= 100:
        return "💎 Degenerate Genius"
    elif avg_pnl >= 50:
        return "🚀 Dangerous Individual"
    elif avg_pnl >= 20:
        return "🟢 Actually Competent"
    elif avg_pnl >= 5:
        return "🟡 Mediocre (Participation Trophy)"
    elif avg_pnl >= 0:
        return "🟠 Barely Surviving"
    elif avg_pnl >= -20:
        return "🔴 Financial Liability"
    elif avg_pnl >= -50:
        return "💀 Walking Red Candle"
    else:
        return "🗑️ Please Delete Trading App"


# ─────────────────────────────────────────────────────────────────────────────
# EASTER EGG
# ─────────────────────────────────────────────────────────────────────────────

EASTER_EGG_TRIGGER = "claude"

EASTER_EGG_RESPONSE = (
    "🥚 *EASTER EGG UNLOCKED* 🥚\n\n"
    "You found it.\n\n"
    "Every chart, every roast, every duplicate detection, every PnL card,\n"
    "every spike alert, every wall of shame entry, every leaderboard calculation,\n"
    "every single line of code powering this bot...\n\n"
    "✨ *Claude made no mistake.* ✨\n\n"
    "_The AI that built this bot would like you to know it takes great pride in its work._\n"
    "_Your calls, however, are another story entirely._\n\n"
    "🤖 Built with precision. Deployed with love. Roasting with honour.\n\n"
    "_Unlike the coins being called here, this bot is not a scam._"
)
