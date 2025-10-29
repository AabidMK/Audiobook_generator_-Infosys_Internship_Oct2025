from text_enricher import TextEnricher

enricher = TextEnricher()

enriched_text = enricher.enrich_and_save("maulik1.txt", "maulik1_enriched.txt")

print("\n Enrichment completed successfully!")
print("Saved enriched file as: maulik1_enriched.txt")
