# Artist Model Attribution

This document tracks neural style transfer models trained on artwork from specific artists, with proper attribution and licensing information.

## Artists & Their Work

### Maurice Pillard Verneuil (1869-1942)
**Style**: Art Nouveau decorative artist, known for flat, stylized natural motifs
**Period**: Late 19th - Early 20th century
**License**: Public Domain (life + 70 years)
**Source**: Downloaded from public domain collections

#### Trained Models:
1. **verneuil_flying_fish** (Verneuil - flying fish.png)
   - Original: "Verneuil - flying fish.png"
   - S3: `s3://nav-untamed-style-transfer-models/style-images/verneuil_flying_fish.png`
   - Training config: 15k images, default weight (1e10)
   - Status: Pending

2. **verneuil_squirrels_2** (Maurice Pillard Verneuil - squirrels 2.jpg)
   - Original: "Maurice Pillard Verneuil Floral Art - squirrels 2.jpg"
   - S3: `s3://nav-untamed-style-transfer-models/style-images/verneuil_squirrels_2.jpg`
   - Training config: 15k images, default weight (1e10)
   - Status: Pending

**Additional Available Works** (not yet trained):
- Peacocks, Blue Parrots, Yellow Eagle, Eagles and Doves
- Forest Deer, Bats, Mullet Fish, Colombes et Lis

### Dahlov Ipcar (1917-2017)
**Style**: American painter, vibrant colorful animals in jungle/savannah settings
**Period**: Mid-20th century modern art
**License**: Check copyright status - may still be under copyright
**Source**: Downloaded from art collections

#### Trained Models:
1. **ipcar_harlequin_jungle** (Dahlov Ipcar - Harlequin Jungle.png)
   - Original: "Dahlov Ipcar - Harlequin Jungle.png"
   - S3: `s3://nav-untamed-style-transfer-models/style-images/ipcar_harlequin_jungle.png`
   - Training config: 15k images, default weight (1e10)
   - Status: Pending

**Additional Available Works** (not yet trained):
- Golden Jungle (needlepoint), Blue Savannah, Valley of Tishnar

### Bruno Liljefors (1860-1939)
**Style**: Swedish wildlife painter, realistic natural scenes
**Period**: Late 19th - Early 20th century
**License**: Public Domain (life + 70 years)
**Source**: Downloaded from public domain collections

#### Trained Models:
1. **liljefors_foxes** (Bruno Liljefors Foxes.jpg)
   - Original: "Bruno Liljefors Foxes.jpg"
   - S3: `s3://nav-untamed-style-transfer-models/style-images/liljefors_foxes.jpg`
   - Training config: 15k images, default weight (1e10)
   - Status: Pending

**Additional Available Works** (not yet trained):
- Foxes 2, Cat, Cat and Bird, Sparrows, Birds in Winter
- Duvhork och orrar (Goshawk and Grouse)

## Training Queue

Priority order after current models complete:
1. mandarin_duck_plumage_1.png (40k, default)
2. verneuil_flying_fish.png (15k, default)
3. verneuil_squirrels_2.jpg (15k, default)
4. ipcar_harlequin_jungle.png (15k, default)
5. liljefors_foxes.jpg (15k, default)

## Copyright & Usage Notes

**Public Domain Works** (Verneuil, Liljefors):
- Free to use for any purpose
- No attribution required but ethically recommended
- Safe for commercial use

**Potentially Protected Works** (Ipcar):
- Dahlov Ipcar died in 2017 (works may still be under copyright)
- Use for personal/educational purposes should be acceptable under fair use
- Consult copyright expert before commercial use
- Consider reaching out to Ipcar estate for licensing

## Model Usage Attribution

When using these models in generated artwork:
```
Style: [Artist Name] ([Artwork Title])
Model: [model_name]
Artist: [Artist Name] ([Birth]-[Death])
Source: Public Domain / Fair Use Educational
```

Example:
```
Style: Maurice Pillard Verneuil (Flying Fish)
Model: verneuil_flying_fish
Artist: Maurice Pillard Verneuil (1869-1942)
Source: Public Domain
```

---

**Last Updated**: 2025-10-18
**Maintained by**: Nikolay + Claude AI
