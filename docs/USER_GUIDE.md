# User Guide

Welcome to **Lumineer** — an AI-powered course discovery system built on 6,645 Coursera courses.

This guide walks through every page and how to get the most out of the AI features.

---

## Getting Started

Lumineer has two modes of use:

| Mode | Pages | Account needed? |
|------|-------|----------------|
| **Browse & Search** | Home, Explore, Course Detail | No |
| **AI Conversation + History** | Chat, My Path, Settings | Yes (free) |

---

## Pages

### Home `/`

The landing page. Shows a value proposition, a quick search bar, and popular courses.

**Quick start:** Type any topic into the search bar and press Enter to go directly to the Explore page with results.

---

### Explore `/explore`

The course catalog — search, filter, and browse with an AI summary.

**Search bar**

Type keywords or a full question:
- `"machine learning Python"` — keyword search
- `"courses to become a data scientist"` — natural language (AI summary appears at top)

Natural language queries that are better handled as a conversation (e.g. "What should I learn first?") will suggest you continue in Chat.

**Filters**

| Filter | Options |
|--------|---------|
| Level | Beginner · Intermediate · Advanced |
| Organization | Type to search providers (e.g. "Stanford", "Google") |
| Min Rating | 3.0+ · 4.0+ · 4.5+ |
| Skills | Type skill tags (e.g. "Python", "TensorFlow") |

Filters combine with AND logic. Results update automatically as you type.

**AI Summary Panel**

When you search, an AI-generated summary appears above the course cards. It synthesizes the search results to directly answer your query. The summary is grounded in the actual search results — it will not invent courses.

**Course cards**

Each card shows: title, organization, level, rating, enrolled count, and top skills. Click a card to go to Course Detail.

---

### Course Detail `/course/:id`

Full information about a single course:

- Title, organization, instructor
- Level and rating
- Enrolled count
- Full description
- Skills covered
- Schedule (estimated time to complete)
- Module structure
- Link to the course on Coursera

---

### Login `/login`

Register or sign in. Only your email and display name are stored. Passwords are never stored in plain text.

After signing in, you can access Chat, My Path, and Settings.

---

### Chat `/chat` *(requires account)*

The main AI interface. Ask anything about courses, your learning goals, or career paths.

**What you can ask:**

| Goal | Example prompt |
|------|---------------|
| Find courses | "Find advanced machine learning courses from Google" |
| Skill gap analysis | "I know Python and SQL. What do I need to become a data scientist?" |
| Learning path | "Create a 3-month plan to learn web development from scratch" |
| Comparison | "What's the difference between these two courses?" |
| Career advice | "Which certifications are most valuable for a DevOps engineer?" |

**Tips for better results:**

- **Be specific:** "Beginner Python for data analysis" gives better results than "Python"
- **Mention your current skills:** The AI uses them to tailor recommendations
- **Include a timeframe:** "I have 2 hours a week for 6 months" helps the Path Agent plan realistically
- **Ask follow-up questions:** The conversation history is preserved within a session

**Session history**

Each conversation is saved as a session. Use the sidebar to:
- Switch between past sessions
- Start a new conversation
- Rename a session (click the title)

---

### My Path `/path` *(requires account)*

Manage and view your saved learning paths.

**Saving a path from Chat:**

When the AI generates a learning path in Chat, a "Save to My Path" button appears. Click it to save the ordered course list.

**Path view:**

Each path shows:
- Goal description
- Ordered course list with level badges
- Links to each course's detail page
- Creation date

---

### Settings `/settings` *(requires account)*

Control how the AI search pipeline works. Changes take effect immediately on the next request.

| Setting | Options | Effect |
|---------|---------|--------|
| **Reranker Strategy** | None · Heuristic · Cross-Encoder | How search results are re-sorted after retrieval |
| **Context Format** | JSON · TOON | How course data is sent to the AI (TOON uses ~50% fewer tokens) |
| **Top K** | 5 · 10 · 20 | Number of courses the AI considers per search |
| **Similarity Threshold** | 0.5–0.9 | Minimum relevance score to include a course |

**Recommended settings for most users:** leave defaults (None / JSON / 10 / 0.7).

**Power user tips:**
- Set **Cross-Encoder** reranker if result quality feels off — it adds ~300ms but improves ranking
- Set **TOON** format if you want the AI to consider more courses within the same token budget
- Lower **Similarity Threshold** to 0.5 if searches return too few results
- Raise it to 0.85+ if you want only highly relevant results

---

## Frequently Asked Questions

**Q: Are the courses free?**
Lumineer links to Coursera. Some courses are free to audit; others require payment or a subscription. Lumineer does not manage enrollments.

**Q: How current is the course data?**
The dataset contains 6,645 courses from a Coursera snapshot. New courses added after the snapshot are not included.

**Q: Why does the AI sometimes not find a specific course I know exists?**
The AI searches semantically — if your query uses very different wording from the course title/description, it may not surface. Try rephrasing, or use a skill tag filter.

**Q: Can I export my learning path?**
Not yet. Copy/paste from the My Path page for now.

**Q: What happens if I don't log in?**
You can browse Explore and Course Detail, and use the AI on the Explore page. Chat history requires an account.

**Q: Is my data private?**
Your email and chat history are stored securely. They are not shared with third parties. Course searches are processed by OpenAI — see OpenAI's privacy policy for their data handling.
