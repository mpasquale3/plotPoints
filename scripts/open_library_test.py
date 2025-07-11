import pandas as pd
import requests
import time





# === API CONFIG ===
TMDB_API_KEY = "d6ad299731d8a3caf6564c0d7816fbd2"
TMDB_BASE_URL = "https://api.themoviedb.org/3/search/multi"
OPENLIB_BASE_URL = "https://openlibrary.org/search.json"


# === CATEGORY MAPPING FUNCTION ===
def map_content_warnings(warning_text):
    if pd.isna(warning_text):
        return ""

    warning_text = warning_text.lower()
    categories = set()

    mapping_keywords = {
        "Violence": ["murder", "violence", "gore", "carceral", "fight", "stabbing", "abuse, violence", "assault", "explosions"],
        "Sexual Violence / SA": ["sa", "sexual assault", "dubcon", "coercion", "noncon", "possessiveness", "rape"],
        "Death / Grief": ["death", "grief", "loss", "suicide", "widow", "funeral", "mourning"],
        "Abuse (Emotional/Physical)": ["abuse", "gaslighting", "manipulation", "neglect"],
        "Mental Health": ["anxiety", "depression", "ptsd", "mental health", "ideation"],
        "Racism / Discrimination": ["racism", "colonial", "white supremacy", "prejudice", "plagiarism"],
        "Classism / Poverty": ["poverty", "classism", "systemic", "gentrification"],
        "Religious Trauma / Cults": ["cult", "religious trauma", "witch trial", "indoctrination"],
        "Sexual Content / Explicit Scenes": ["explicit", "sex scenes", "erotica", "fetish", "body horror"],
        "Addiction / Substance Use": ["addiction", "alcohol", "drinking", "drug"],
        "Family Conflict / Trauma": ["family trauma", "parent", "adoption", "legacy", "inheritance"],
        "Medical / Institutional Abuse": ["medical", "hospital", "incarceration", "surveillance", "institutional"],
        "Supernatural Horror": ["possession", "occult", "ghost", "curses", "witch", "supernatural"],
        "Disability / Neurodivergence": ["ableism", "neurodivergent", "disability", "autism", "brain condition"],
        "War / Political Oppression": ["war", "fascism", "political violence", "dictatorship", "protest", "nazi"]
    }

    for category, keywords in mapping_keywords.items():
        for keyword in keywords:
            if keyword in warning_text:
                categories.add(category)
                break  # prevent duplicate matching

    return ", ".join(sorted(categories)) if categories else "Uncategorized"

# === Load CSV ===
df = pd.read_csv("C:/Users/kenna/OneDrive/Documents/PlotPoints/data/plotPoints.csv")
df["Adaptation"] = df["Adaptation"].fillna("")
df["First_Publish_Year"] = df["First_Publish_Year"].fillna("")
df["Publisher"] = df["Publisher"].fillna("")

# === Movie DB Adaptation Lookup ===
def check_adaptation(title):
    params = {
        "query": title,
        "include_adult": "false",
        "language": "en-US",
        "page": 1,
        "api_key": TMDB_API_KEY
    }
    response = requests.get(TMDB_BASE_URL, params=params)
    if response.status_code == 200:
        results = response.json().get("results", [])
        for result in results:
            media_type = result.get("media_type", "")
            if media_type == "movie":
                return "Film"
            elif media_type == "tv":
                return "TV"
        return "In Dev" if results else "Not Yet Considered"
    else:
        return "Not Yet Considered"

# === Open Library Metadata Lookup ===
def get_open_library_data(title, author):
    params = {
        "title": title,
        "author": author,
    }
    response = requests.get(OPENLIB_BASE_URL, params=params)
    if response.status_code == 200:
        docs = response.json().get("docs", [])
        if docs:
            top = docs[0]
            return {
                "first_publish_year": top.get("first_publish_year", ""),
                "publisher": top.get("publisher", [""])[0],
                
            }
    return {"first_publish_year": "", "publisher": "" }

# === Loop and Enrich ===
for i, row in df.iterrows():
    title = row["Title"]
    author = row["Author"]
    print(f"🔍 Checking: {title} by {author}")

    # Adaptation only if blank
    if row["Adaptation"].strip() == "":
        df.at[i, "Adaptation"] = check_adaptation(title)

    # Open Library enrichment
    result = get_open_library_data(title, author)

    # Fill in missing values only
    if row["First_Publish_Year"] == "":
        df.at[i, "First_Publish_Year"] = result["first_publish_year"]
    if row["Publisher"] == "":
        df.at[i, "Publisher"] = result["publisher"]

    

    time.sleep(0.5)  

    # === Map Clean Content Warning Categories ===
df["Content_Warning_Category"] = df["Content_Warnings"].apply(map_content_warnings)

# === DIVERSITY CATEGORY MAPPING FUNCTION ===
def map_diversity_rep(rep_text):
    if pd.isna(rep_text):
        return ""

    rep_text = rep_text.lower()
    categories = set()

    mapping_keywords = {
        "Black / African": ["black", "african", "afro-caribbean"],
        "Latinx": ["latinx", "latine", "latina", "queer latinx", "trans latinx"],
        "Asian / South Asian": ["asian", "asian-american", "south asian", "southeast asian", "aapi"],
        "Indigenous": ["indigenous", "native american", "first nations"],
        "Queer Identity": ["queer", "lgbtq", "implied queer", "outing fears", "homophobia", "queer identity", "queer bipoc"],
        "Gender Identity": ["trans", "gender dysphoria", "transphobia", "nonbinary", "gender"],
        "Neurodivergent": ["neurodiverse", "adhd", "autism", "subtle neurodivergence", "mental health"],
        "Disability / Illness": ["illness", "aging", "chronic", "disability"],
        "Ethnic & Cultural Identity": ["jewish", "irish", "swedish", "finnish", "multiracial"],
        "Intersectional / Mixed": ["queer black", "queer latinx", "queer bipoc", "queer aapi", "racism", "alcoholism", "mixed"]
    }

    for category, keywords in mapping_keywords.items():
        for keyword in keywords:
            if keyword in rep_text:
                categories.add(category)
                break  # avoid duplicate matching

    return ", ".join(sorted(categories)) if categories else "Uncategorized"

# === Map Diversity Categories from Diversity_Rep ===
df["Diversity_Category"] = df["Diversity_Rep"].apply(map_diversity_rep)


# === GENRE CATEGORY AND SUBTAGS MAPPING ===
def map_genre_tags(tag_text):
    if pd.isna(tag_text):
        return "", "", "", "", ""

    tag_text = tag_text.lower()
    tropes = set()
    themes = set()
    formats = set()

    genre_mapping = {
        "Fantasy": ["fantasy", "urban fantasy", "myth", "fairy tale", "magic", "sff"],
        "Romantasy": ["romantasy"],
        "Science Fiction": ["sci-fi", "science fiction", "afrofuturism", "time travel", "space", "alien", "dystopian tech"],
        "Horror": ["horror", "haunted", "gothic", "psychological", "slasher"],
        "Romance": ["romance", "smut", "contemporary romance", "dark romance", "taboo romance"],
        "Mystery / Thriller": ["mystery", "thriller", "suspense", "noir", "cozy"],
        "Contemporary Fiction": ["contemporary", "slice of life", "feel-good"],
        "Historical Fiction": ["historical", "wwii", "alt-history", "resistance"],
        "Speculative Fiction": ["speculative", "dystopia", "spec fic"],
        "Young Adult (YA)": ["ya", "young adult"],
        "New Adult (NA)": ["new adult", "na"],
        "Graphic Works": ["graphic novel", "graphic memoir", "visual", "manga"],
        "Poetry / Experimental": ["verse", "poetry", "experimental", "epistolary"],
        "Nonfiction / Essay": ["nonfiction", "essay", "memoir"],
        "LGBTQ+ Lit": ["queer lit", "lgbtq", "queer fiction"]
    }

    trope_keywords = {
        "Enemies-to-Lovers": ["enemies-to-lovers", "enemies to lovers"],
        "Trials": ["trials", "competitions", "tournament"],
        "Dragons": ["dragons"],
        "Vampires": ["vampires"],
        "Secret Societies": ["secret societies", "magical university"],
        "Why Choose": ["why choose"],
        "Possessive Hero": ["possessive hero", "alpha male"],
        "Retelling": ["retelling"],
        "Chosen One": ["chosen one", "destiny"],
        "Forbidden Romance": ["forbidden romance"]
    }

    theme_keywords = {
        "Found Family": ["found family", "chosen family"],
        "Grief": ["grief", "mourning", "loss"],
        "Trauma Recovery": ["trauma", "healing", "therapy"],
        "Feminist Lit": ["feminist", "patriarchy"],
        "Queer Lit": ["queer lit", "queer identity"],
        "Political": ["political", "revolution", "resistance"],
        "Healing": ["healing"],
        "Dark Academia": ["dark academia"],
        "Satire": ["satire"],
        "Oppression / Resistance": ["oppression", "resistance"]
    }

    format_keywords = {
        "Graphic Novel": ["graphic novel", "visual", "manga"],
        "Novella": ["novella"],
        "Verse": ["verse"],
        "Anthology": ["anthology", "short stories"],
        "Hybrid": ["hybrid"],
        "Memoir": ["memoir"],
        "Epistolary": ["epistolary"],
        "Smut": ["smut", "spice"],
        "Short Reads": ["short reads", "quick read"],
        "Visual Poetry": ["visual poetry"]
    }

    #  === ONE GENRE ONLY Return the first match ===
    primary_genre = "Uncategorized"
    for genre, keywords in genre_mapping.items():
        for keyword in keywords:
            if keyword in tag_text:
                primary_genre = genre
                break
        if primary_genre != "Uncategorized":
            break

    # Subtags multi-match
    for label, keywords in trope_keywords.items():
        for keyword in keywords:
            if keyword in tag_text:
                tropes.add(label)
                break

    for label, keywords in theme_keywords.items():
        for keyword in keywords:
            if keyword in tag_text:
                themes.add(label)
                break

    for label, keywords in format_keywords.items():
        for keyword in keywords:
            if keyword in tag_text:
                formats.add(label)
                break

    combined_subtags = sorted(tropes | themes | formats)

    return (
        primary_genre,
        ", ".join(sorted(tropes)),
        ", ".join(sorted(themes)),
        ", ".join(sorted(formats)),
        ", ".join(combined_subtags)
    )


# === Apply Genre Mapping ===
genre_results = df["Genre Tag(s)"].apply(map_genre_tags)
df[["Genre_Category", "Genre_Tropes", "Genre_Themes", "Genre_Format", "Genre_Subtags"]] = pd.DataFrame(genre_results.tolist(), index=df.index)




#==== Trend Category Mapping ===
def group_trend_category(category_text):
    if pd.isna(category_text):
        return ""

    text = category_text.lower().strip()

    if "adaptation" in text or "movie" in text or "tv" in text:
        return "Adaptation / Movie Buzz"
    elif "algorithmic" in text or "virality" in text or "general" in text:
        return "Viral Momentum"
    elif "new release" in text:
        return "New Release Buzz"
    elif "series" in text:
        return "Series Momentum"
    elif "tiktok" in text or "tropes" in text:
        return "Trending Tropes (BookTok)"
    elif "romantasy" in text:
        return "Romantasy Resurgence"
    elif "emotional" in text or "trauma" in text:
        return "Emotional / Trauma Themes"
    elif "queer" in text or "identity" in text:
        return "Queer / Identity-Based Discovery"
    elif "classic" in text or "reprint" in text or "reread" in text:
        return "Classic Revisit / Reread Trend"
    elif "indie" in text or "self-pub" in text or "small press" in text:
        return "Indie Author Buzz"
    elif "bipoc" in text or "black" in text or "latinx" in text:
        return "BIPOC Author Buzz"
    elif "alt" in text or "experimental" in text or "zine" in text:
        return "Alt / Experimental Lit Trend"
    else:
        return "Other / Uncategorized"


df["Trend_Category"] = df["Trend_Category"].apply(group_trend_category)


# === Save File ===
df.to_csv("C:/Users/kenna/OneDrive/Documents/PlotPoints/data/plotPoints_updated.csv", index=False)
print("\n Done! File saved to: data/plotPoints_updated.csv")
