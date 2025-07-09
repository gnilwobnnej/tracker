import requests

def get_scientific_names(query, max_records=1000):
    scientific_names = set()
    limit = 100
    offset = 0

    while offset < max_records:
        url = f"https://api.gbif.org/v1/occurrence/search?q={query}&year=2025&limit={limit}&offset={offset}"
        response = requests.get(url)
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            break

        for species in results:
            name = species.get("scientificName")
            if name:
                scientific_names.add(name)

        offset += limit

    return scientific_names

print("""popular class types: \n Amphibians = Amphibia \n Birds = Aves \n Fish = Osteichthyes
 Mammals = Mammalia \n Reptiles = Reptilia \n Crabs, lobsters, and barnacles = Crustaceans \n 
      """)

# Ask the user for input
query = input("Enter a class type: ").strip()
max_records = input("How many records should we search through? (e.g., 1000): ").strip()

# Validate and convert max_records
try:
    max_records = int(max_records)
except ValueError:
    print("Invalid number entered. Defaulting to 1000.")
    max_records = 1000

# Search and display results
names = get_scientific_names(query, max_records=max_records)

print(f"\nFound {len(names)} unique scientific names for '{query}':\n")
for name in sorted(names):
    print(name)