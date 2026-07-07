# Research Campuses Directory

## Overview

Research Campuses are the trusted research source repositories for each of the 13 schools in the Chimera Development Cycle. Each campus maintains seed sources, quality ratings, and discovery protocols that accelerate reference fidelity and ensure consistent educational foundations before creative research begins.

**Campus + 1 Rule:** Foundation first. Discovery always. Campus + 1 — query the campus for trusted sources, then discover one additional reference to expand the knowledge base.

---

## The 12 Research Campuses (Schools)

### Campus 1: Game Development School
*Focus:* Level design, lighting, environment art, visual storytelling, game feel

**Seed Sources:**
- GDC Vault: Level Design Principles
- Unreal Engine Documentation: Lighting for Games
- ArtStation Environment Art Pipelines
- Game Developer Magazine: Visual Storytelling

**Quality Ratings:**
- A+: Official Epic Games documentation, GDC presentations from senior developers
- B+: Industry articles from Game Developer, Polygon, IGN Creative
- C: General gaming blogs, unverified tutorials

### Campus 2: Art School
*Focus:* Color theory, composition, form/mass, light/shadow, material rendering

**Seed Sources:**
- Color Theory for Artists (online courses)
- Composition Principles in Fine Art
- PBR Materials Explained by Artists
- Form and Silhouette Design Principles

**Quality Ratings:**
- A+: Academic art resources, professional artist tutorials (Proko, Draw.io)
- B+: ArtStation tutorials, YouTube art education channels
- C: General design blogs, unverified color theory guides

### Campus 3: Film School
*Focus:* Cinematography, three-point lighting, production design

**Seed Sources:**
- American Society of Cinematographers (ASC) guidelines
- Three-Point Lighting Setup Tutorials
- Film Production Design Principles
- Cinematography Camera Work Principles

**Quality Ratings:**
- A+: ASC publications, professional cinematographer tutorials
- B+: Film school resources, professional director guides
- C: General photography blogs, amateur filmmaking guides

### Campus 4: Architecture School
*Focus:* Spatial design, materiality, lighting design

**Seed Sources:**
- Architectural Digest Design Principles
- Spatial Design for Interiors
- Architectural Lighting Design Guidelines
- Materiality in Modern Architecture

**Quality Ratings:**
- A+: Professional architecture publications (ArchDaily, Architizer)
- B+: University architecture department resources
- C: General home design blogs, interior decorating sites

### Campus 5: Engineering School
*Focus:* Spacecraft design, industrial design, form follows function

**Seed Sources:**
- NASA Technical Reports
- Industrial Design Principles (Form Follows Function)
- Spacecraft Design Constraints and Requirements
- Engineering Form and Function Case Studies

**Quality Ratings:**
- A+: Official NASA documentation, engineering textbooks
- B+: Professional engineering society publications
- C: General science blogs, speculative engineering articles

### Campus 6: Unreal Engine Craft School
*Focus:* Modeling Mode, console commands, MCP geometry tools, shape creation

**Seed Sources:**
- Unreal Engine 5 Documentation: Modeling Mode
- UE5 Sculpting Tools Tutorials
- MCP Geometry Tools Documentation
- Console Command References

**Quality Ratings:**
- A+: Official Epic Games documentation, verified MCP pathway docs
- B+: Community tutorials that have been verified against official docs
- C: Unverified YouTube tutorials, outdated engine version guides

### Campus 7: Spatial Reasoning School
*Focus:* 3D composition, grid systems, distance/scale, spatial relationships

**Seed Sources:**
- 3D Composition Principles for Games
- Modular Grid Design for Games
- Spatial Relationship Guidelines in Level Design
- Distance and Scale in Virtual Environments

**Quality Ratings:**
- A+: Academic game design resources, professional level design guides
- B+: Industry level design articles, GDC spatial reasoning talks
- C: General 3D modeling tutorials without spatial context

### Campus 8: Iteration School
*Focus:* Michelangelo Procedure, failure protocol, refinement process

**Seed Sources:**
- Michelangelo Carving Process Documentation
- Iterative Design Process Refinement Guides
- Failure Protocol in Creative Industries
- The Michelangelo Procedure in Modern Practice

**Quality Ratings:**
- A+: Historical documentation of Michelangelo's process, verified iteration studies
- B+: Professional creative industry refinement guides
- C: General productivity or creativity blogs

### Campus 9: Emotion-to-Parameter School
*Focus:* Mapping feelings to technical values (lighting, materials, sound, space)

**Seed Sources:**
- How Lighting Creates Mood in Film
- Color Temperature and Emotion Psychology
- How Materials Affect Mood in Interior Design
- Emotional Sound Design Principles

**Quality Ratings:**
- A+: Academic psychology studies on color/emotion, professional film lighting guides
- B+: Professional game audio/lighting design resources
- C: General mood or atmosphere blogs

### Campus 10: Reference Management School
*Focus:* Organization, avoiding duplication, cross-referencing, reference decay

**Seed Sources:**
- Graphify Knowledge Graph Documentation
- Reference Organization Systems in Creative Industries
- Cross-Referencing Techniques for Research
- Reference Decay and Verification Protocols

**Quality Ratings:**
- A+: Official Chimera documentation, verified knowledge graph practices
- B+: Professional research organization guides
- C: General note-taking or organization blogs

### Campus 11: Creativity School
*Focus:* Combinatorial creativity, extrapolation, constraints as creativity

**Seed Sources:**
- Combinatorial Creativity Research Papers
- Constraints as Creativity in Design
- Extrapolation Techniques Across Domains
- The Idea Log and Creative Documentation

**Quality Ratings:**
- A+: Academic creativity research, verified design methodology papers
- B+: Professional creative industry methodology guides
- C: General creativity or brainstorming blogs

### Campus 12: Collaboration School
*Focus:* Presenting options, asking for guidance, mirror protocol

**Seed Sources:**
- Mirror Protocol in Creative Collaboration
- Presenting Options to Stakeholders
- Incorporating Feedback in Creative Industries
- Asking for Guidance Effectively

**Quality Ratings:**
- A+: Professional collaboration methodology resources, verified communication guides
- B+: Industry teamwork and collaboration guides
- C: General workplace communication blogs

---

## Discovery Loop Protocol

The Discovery Loop ensures that every research session not only consumes existing campus sources but also discovers and records new ones:

1. **Query Campus First:** Before any creative research, query the relevant campus for seed sources using `g.query("campus", relevant_school)`
2. **Study Seed Sources:** Extract principles and parameters from the highest-rated (A+) sources first
3. **Discover +1 Reference:** Find at least one additional reference that supports or expands upon the campus seeds
4. **Verify Quality:** Assess the new reference against the quality rating system
5. **Record Discovery:** Add the new reference to the campus with appropriate quality rating and seed status
6. **Update Feature Ledger:** Link the new discovery to relevant features in the ledger

---

## Quality Rating System

All references and sources are rated using a three-tier quality system:

### A+ (Premium/Verified)
- Official documentation from authoritative sources (Epic Games, NASA, ASC, etc.)
- Academic research papers or university-level educational resources
- Verified MCP pathways and documented Graphify patterns
- GDC presentations from senior industry professionals

**Usage:** Primary source for parameter extraction and principle validation. Always prefer A+ sources when available.

### B (Good/Verified)
- Industry publications from reputable sources (Game Developer, ArchDaily, etc.)
- Professional tutorials that have been verified against official documentation
- Community resources with high verification rates in the Graphify DNA
- Verified case studies and project post-mortems

**Usage:** Secondary source for additional context and alternative perspectives. Use when A+ sources are insufficient.

### C (Unverified/Reference Only)
- General blogs, amateur tutorials, unverified guides
- Sources that have not been verified against official documentation
- Speculative or opinion-based content

**Usage:** For inspiration only. Never use for parameter extraction or principle validation without verification against A+ or B sources.

---

## Campus Query Examples

### Querying a Campus for Research Sources

```python
# Get trusted research sources for Game Development School
g.query("campus", "game_development")

# Get seed sources for Emotion-to-Parameter mapping
g.query("campus", "emotion_to_parameter")

# Get reference materials for Unreal Engine Craft
g.query("campus", "unreal_engine_craft")
```

### Expected Query Response Format

A campus query returns:
- List of seed sources with URLs or references
- Quality ratings for each source (A+, B, C)
- Associated principles and concepts
- Linked features in the Feature Ledger
- Previous discoveries and mutations related to this campus

---

## Agent Contribution Instructions

### Adding New Seed Sources to a Campus

1. **Verify the Source:** Ensure the new source meets A+ or B quality standards
2. **Extract Principles:** Document the specific principles or parameters the source provides
3. **Link to Features:** Identify which features in the Feature Ledger would benefit from this source
4. **Record in Graphify:** Use `g.mutate("campus_source_added", {campus, source, quality_rating, principles})`
5. **Update Documentation:** If the source represents a new category of reference, update the relevant campus section

### Discovering and Recording New Campuses

If you identify a new school or campus that should be added to the 13 schools:

1. **Document the Principles:** What specific knowledge does this campus provide?
2. **Identify Seed Sources:** List the authoritative sources for this domain
3. **Map to Features:** Which spiral loop features would benefit from this campus?
4. **Submit for Review:** Record the proposed campus in Graphify with status `proposed_campus`
5. **Await Approval:** The human reviewer will approve or reject the new campus addition

### Maintaining Reference Decay

Periodically (every 30 days or when a feature is re-verified):

1. **Re-verify Old Sources:** Check if previously recorded A+ sources still hold true
2. **Update Quality Ratings:** Adjust ratings if sources have been superseded by newer documentation
3. **Archive Outdated References:** Mark sources as `deprecated` if they no longer reflect current practices
4. **Record Decay Mutations:** Use `g.mutate("reference_decay", {source, old_rating, new_rating, reason})`

---

## Integration with the Development Cycle

Research Campuses are integrated into the development cycle at these key points:

1. **Phase 0 (Foundation):** Query Research Campuses for trusted sources before creating/updating the Feature Ledger
2. **Phase 1 (Creative Research - Campus-Driven):** Primary source for reference extraction and parameter discovery
3. **Phase 6 (Iterate):** Return to campuses when fundamentals are missing or when discovering new principles

The campus system ensures that every creative research phase is grounded in trusted, verified sources rather than speculative or unverified information. This maintains the integrity of the spiral growth pattern and ensures that each loop builds on a solid educational foundation.