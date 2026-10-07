# Repository access and setup

Repository: https://github.com/ph2606/epl-sports-betting-final-project

This is a private academic working repository for the Statistical Arbitrage
final project. It contains the complete final-project folder, including earlier
proposal/reference work and the EPL acquisition snapshot. Unrelated course
assignments and separate trading projects are outside this repository.

## Complete checkout

Install Git and Git LFS, then run:

```powershell
git lfs install
git clone https://github.com/ph2606/epl-sports-betting-final-project.git
cd epl-sports-betting-final-project
git lfs pull
python -m pip install -r epl_data/requirements.txt
```

Large files are stored using Git LFS. A GitHub source ZIP can contain LFS pointer
files instead of those datasets; use the commands above for a complete checkout.
The `.gitattributes` rules preserve source file bytes without line-ending
conversion so that the saved SHA256 hashes remain useful.

The [EPL README](epl_data/README.md),
[source guide](epl_data/SOURCE_GUIDE.md) and
[dataset catalog](epl_data/metadata/dataset_catalog.csv) explain the available
data. Open the workbook or executed notebook to start exploring it.

## Source rights

Repository access does not confer a new license on third-party data, papers,
logos or other source material. Their original terms remain in force. No blanket
open-source or open-data license is applied to this collection.

Keep the repository private. Before making it public, sharing underlying
datasets with additional users, or using them commercially, review each
provider's terms and obtain any required permission. In particular, StatsBomb's
saved Public Data User Agreement restricts third-party provision and
redistribution of underlying data and requires its logo on published analysis.
Football-Data's published terms specify private individual use and exclusions
for commercial/data-training products and automated bots or scrapers. Links,
licenses and acquisition details are retained with the source snapshots and
metadata. The CC0 declaration for the historical Transfermarkt archive does not
apply to the separately downloaded current Transfermarkt pages.

The snapshot records original retrieval and coverage limitations; a repository
upload date does not turn historical or stale provider fields into current
observations.
