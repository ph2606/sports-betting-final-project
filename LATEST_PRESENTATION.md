# Latest EPL presentation

**Short version — October 21, 2026.** Open **`presentations/latest/`**:

- [Short presentation — editable PowerPoint](presentations/latest/EPL_Project_Presentation_Short.pptx)
- [Short presentation — PDF](presentations/latest/EPL_Project_Presentation_Short.pdf)
- [Short presentation — speaker notes](presentations/latest/EPL_Presentation_Short_Notes.md)
- [All 116 strategies explained in plain language — CSV](presentations/latest/EPL_Presentation_Short_Rules.csv)

The presentation has **six main slides**:

1. What has been implemented.
2. Money progression of all 116 strategies, starting with 100,000 each.
3. Best learned prediction model: description, trading rules and results.
4. Simplest model: description, trading rules and results.
5. One team-data model: description, trading rules and results.
6. One player-data model: description, trading rules and results.

Everything after slide 6 is the requested appendix. It explains the capital
rules, then every strategy's model, entry condition, stake per trade, limits
and price source. Paired strategies share the same entry rule but their
individual stake settings are listed separately.

The model pages state that a fixed 1,000 stake is **1% of the initial 100,000**.
The appendix also explains percentage-of-current-cash staking, Kelly sizing,
per-bet caps, total date caps and scaling requests to available cash.

The graph uses the common 2025/26 season for all 116 strategies. Model pages
label their four-year statistics explicitly. "Best model" means the lowest
prediction loss among the learned models; it does not mean the largest
trading account.

The original full PowerPoint was open and locally modified, so it remains
untouched. The new files use the **`_Short`** filename. For reproduction, see
[epl_presentation/CONCISE.md](epl_presentation/CONCISE.md).
