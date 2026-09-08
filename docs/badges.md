# Badge catalogue

Every badge below ships with the package and is active out of the box. Nothing here needs config. Use `catalogue` to narrow the set, and `badges` to recolour an entry or add your own.

Generated from `CATALOGUE` in `src/markdown_badges/catalogue.py` by `scripts/gen_badges.py`. Edit the catalogue, not this file.

![Every badge in the catalogue, rendered](img/catalogue.png)

> [!NOTE]
> Only `priority` badges carry a severity rank. `priority_of` and `rank_of` ignore `status` and `branding` badges entirely; use `badges_in` to get every badge on a line whatever its type.

## Priority

| Keyword | Value | Text | Notes |
| --- | --- | --- | --- |
| `!trivial` | `#78909c` | `#000` | Nice to have. |
| `!low` | `#2e7d32` | `#fff` | Green. |
| `!medium` | `#f9a825` | `#000` | Amber. |
| `!high` | `#ef6c00` | `#000` | Orange. |
| `!critical` | `#d32f2f` | `#fff` | Red. |
| `!blocker` | `#7b1fa2` | `#fff` | Work that cannot start. |

## Status

| Keyword | Value | Text | Notes |
| --- | --- | --- | --- |
| `!todo` | `#1565c0` | `#fff` | Not started. |
| `!wip` | `#0277bd` | `#fff` | In progress. |
| `!review` | `#6a1b9a` | `#fff` | Waiting on a reviewer. |
| `!blocked` | `#b71c1c` | `#fff` | Waiting on someone else. |
| `!approved` | `#2e7d32` | `#fff` | Signed off, not yet shipped. |
| `!done` | `#37474f` | `#fff` | Finished. |
| `!onhold` | `#8d6e63` | `#fff` | Paused on purpose. |
| `!experimental` | `#00838f` | `#000` | Not stable yet. |
| `!deprecated` | `#5d4037` | `#fff` | On the way out. |

## Branding

| Keyword | Value | Text | Notes |
| --- | --- | --- | --- |
| `!gitlab` | `#7759c2 plus icon CSS` | `#fff` | GitLab purple. |
| `!github` | `#181717 plus icon CSS` | `#fff` | GitHub near-black. |
| `!claude` | `#d97757 plus icon CSS` | `#000` | Claude coral, dark mark. |
| `!docker` | `#1d63ed plus icon CSS` | `#fff` | Docker blue, white whale. |
| `!aws` | `#232f3e` | `#fff` | AWS squid ink. No mark. |

## Narrowing the catalogue

```toml
[project.markdown_extensions.markdown_badges]
catalogue = ["priority", "status"]   # drop the branding badges
```

## Adding your own

```toml
[project.markdown_extensions.markdown_badges.badges.priority]
showstopper = "#000000"   # a new priority, ranked above every catalogue one
critical = "#8e0000"      # an existing name: recolours it, keeping its rank
```

For a logo badge, add the mark as a single-path SVG to `ICONS` in `src/markdown_badges/catalogue.py` and build the value with `_icon_value`. Pick the base colour and the icon fill together: the badge text colour comes from the base, so a white mark needs a base that resolves to white text.
