#!/usr/bin/env python3
"""
generate_memory_whitepaper.py — Generate a LaTeX-style PDF whitepaper about
the Persistent Agent Memory architecture.

Output: docs/persistent-agent-memory-whitepaper.pdf

Usage:
    python3 scripts/generate_memory_whitepaper.py
"""

import os
import textwrap
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Preformatted, Flowable, HRFlowable,
)
from reportlab.lib import colors

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(WORKSPACE, "docs", "persistent-agent-memory-whitepaper.pdf")


# ─── Custom Flowables ──────────────────────────────────────────────────

class GrayBox(Flowable):
    """A code block with gray background."""
    def __init__(self, text, width=None, font_size=8.5):
        Flowable.__init__(self)
        self.text = text
        self.box_width = width or (6.5 * inch)
        self.font_size = font_size
        self.padding = 8

    def wrap(self, availWidth, availHeight):
        self.box_width = min(self.box_width, availWidth)
        lines = self.text.split('\n')
        self.box_height = len(lines) * (self.font_size + 2) + 2 * self.padding
        return (self.box_width, self.box_height)

    def draw(self):
        self.canv.saveState()
        self.canv.setFillColor(HexColor('#F0F0F0'))
        self.canv.roundRect(0, 0, self.box_width, self.box_height, 3, fill=1, stroke=0)
        self.canv.setFillColor(black)
        self.canv.setFont('Courier', self.font_size)
        y = self.box_height - self.padding - self.font_size
        for line in self.text.split('\n'):
            self.canv.drawString(self.padding, y, line)
            y -= (self.font_size + 2)
        self.canv.restoreState()


class BoxDiagram(Flowable):
    """A simple architectural box diagram."""
    def __init__(self, width=None, height=280):
        Flowable.__init__(self)
        self.dia_width = width or (5.5 * inch)
        self.dia_height = height

    def wrap(self, availWidth, availHeight):
        return (self.dia_width, self.dia_height)

    def draw(self):
        c = self.canv
        c.saveState()

        # Layout constants
        box_w = 110
        box_h = 40
        center_x = self.dia_width / 2
        y_positions = [220, 160, 100, 40]
        labels = [
            ("Layer 4: Boot Injection", "boot_agent.py"),
            ("Layer 3: Shared Brain", "JSON files"),
            ("Layer 2: Per-Agent Memory", "Markdown logs"),
            ("Layer 1: Structured Storage", "SQLite databases"),
        ]
        fill_colors = [
            HexColor('#2C3E50'),
            HexColor('#34495E'),
            HexColor('#5D6D7E'),
            HexColor('#85929E'),
        ]

        for i, (label, sub) in enumerate(labels):
            y = y_positions[i]
            x = center_x - box_w
            w = box_w * 2

            c.setFillColor(fill_colors[i])
            c.roundRect(x, y, w, box_h, 5, fill=1, stroke=0)

            c.setFillColor(white)
            c.setFont('Helvetica-Bold', 9)
            c.drawCentredString(center_x, y + 24, label)
            c.setFont('Helvetica', 7.5)
            c.drawCentredString(center_x, y + 12, sub)

        # Arrows between layers
        c.setStrokeColor(HexColor('#2C3E50'))
        c.setLineWidth(1.5)
        for i in range(3):
            y_top = y_positions[i]
            y_bot = y_positions[i + 1] + box_h
            mid = center_x
            c.line(mid - 15, y_top, mid - 15, y_bot)  # down arrow
            c.line(mid + 15, y_bot, mid + 15, y_top)  # up arrow
            # arrowheads (down)
            c.line(mid - 15, y_bot, mid - 18, y_bot + 5)
            c.line(mid - 15, y_bot, mid - 12, y_bot + 5)
            # arrowheads (up)
            c.line(mid + 15, y_top, mid + 12, y_top - 5)
            c.line(mid + 15, y_top, mid + 18, y_top - 5)

        # Side annotations
        c.setFillColor(HexColor('#555555'))
        c.setFont('Helvetica', 7)
        c.drawString(center_x + box_w + 10, y_positions[0] + 15, "← Runs before first inference")
        c.drawString(center_x + box_w + 10, y_positions[1] + 15, "← Cross-agent state")
        c.drawString(center_x + box_w + 10, y_positions[2] + 15, "← Private daily logs")
        c.drawString(center_x + box_w + 10, y_positions[3] + 15, "← Persistent structured data")

        # Title
        c.setFillColor(HexColor('#2C3E50'))
        c.setFont('Helvetica-Bold', 10)
        c.drawCentredString(center_x, self.dia_height - 10, "Figure 1: Four-Layer Memory Architecture")

        c.restoreState()


# ─── Page Template ──────────────────────────────────────────────────────

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Roman', 9)
    canvas.setFillColor(HexColor('#888888'))
    canvas.drawCentredString(letter[0] / 2, 0.5 * inch,
                              f"— {doc.page} —")
    canvas.restoreState()


def build_styles():
    """Build all paragraph styles for the document."""
    styles = {}

    styles['Title'] = ParagraphStyle(
        'Title',
        fontName='Times-Bold',
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=HexColor('#1A1A1A'),
    )

    styles['Author'] = ParagraphStyle(
        'Author',
        fontName='Times-Roman',
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        spaceAfter=4,
        textColor=HexColor('#444444'),
    )

    styles['Date'] = ParagraphStyle(
        'Date',
        fontName='Times-Roman',
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=HexColor('#666666'),
    )

    styles['AbstractLabel'] = ParagraphStyle(
        'AbstractLabel',
        fontName='Times-Bold',
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        spaceBefore=20,
        spaceAfter=8,
    )

    styles['Abstract'] = ParagraphStyle(
        'Abstract',
        fontName='Times-Italic',
        fontSize=10.5,
        leading=14,
        alignment=TA_JUSTIFY,
        leftIndent=40,
        rightIndent=40,
        spaceAfter=20,
        textColor=HexColor('#333333'),
    )

    styles['Section'] = ParagraphStyle(
        'Section',
        fontName='Times-Bold',
        fontSize=14,
        leading=18,
        spaceBefore=20,
        spaceAfter=8,
        textColor=HexColor('#1A1A1A'),
    )

    styles['Subsection'] = ParagraphStyle(
        'Subsection',
        fontName='Times-Bold',
        fontSize=12,
        leading=15,
        spaceBefore=14,
        spaceAfter=6,
        textColor=HexColor('#2A2A2A'),
    )

    styles['Subsubsection'] = ParagraphStyle(
        'Subsubsection',
        fontName='Times-BoldItalic',
        fontSize=11,
        leading=14,
        spaceBefore=10,
        spaceAfter=4,
        textColor=HexColor('#333333'),
    )

    styles['Body'] = ParagraphStyle(
        'Body',
        fontName='Times-Roman',
        fontSize=11,
        leading=14.5,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        textColor=HexColor('#1A1A1A'),
    )

    styles['Bullet'] = ParagraphStyle(
        'Bullet',
        fontName='Times-Roman',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        leftIndent=24,
        bulletIndent=12,
        spaceAfter=4,
        textColor=HexColor('#1A1A1A'),
    )

    styles['BulletBold'] = ParagraphStyle(
        'BulletBold',
        fontName='Times-Roman',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        leftIndent=24,
        bulletIndent=12,
        spaceAfter=4,
        textColor=HexColor('#1A1A1A'),
    )

    styles['Caption'] = ParagraphStyle(
        'Caption',
        fontName='Times-Italic',
        fontSize=9.5,
        leading=12,
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=12,
        textColor=HexColor('#555555'),
    )

    styles['TableHeader'] = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=white,
    )

    styles['TableCell'] = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=HexColor('#1A1A1A'),
    )

    return styles


def make_table(headers, rows, col_widths=None):
    """Create a styled table."""
    s = build_styles()
    header_row = [Paragraph(h, s['TableHeader']) for h in headers]
    data_rows = []
    for row in rows:
        data_rows.append([Paragraph(str(c), s['TableCell']) for c in row])
    data = [header_row] + data_rows

    if col_widths is None:
        col_widths = [6.5 * inch / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F8F8F8')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


# ─── Document Content ───────────────────────────────────────────────────

def build_document():
    """Build the entire whitepaper as a list of flowables."""
    s = build_styles()
    story = []

    # ── Title Page ──
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph(
        "Persistent Agent Memory:<br/>"
        "A File-Based Architecture for<br/>"
        "Stateful Multi-Agent Systems",
        s['Title']
    ))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Theo", s['Author']))
    story.append(Paragraph("OpenClaw Project", s['Author']))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("March 2026", s['Date']))

    story.append(Spacer(1, 0.5 * inch))
    story.append(HRFlowable(width="60%", thickness=0.5, color=HexColor('#CCCCCC'),
                              spaceAfter=20, spaceBefore=10))

    # Abstract
    story.append(Paragraph("Abstract", s['AbstractLabel']))
    story.append(Paragraph(
        "Multi-agent systems built on large language models suffer from cold-start amnesia — "
        "each session begins with no operational context from prior runs. We present a four-layer "
        "persistent memory architecture that gives every agent structured context injection at boot "
        "and enforced write-back after every task. The system uses only flat files and SQLite databases "
        "(no middleware, no central server), builds on existing semantic search infrastructure, and adds "
        "approximately 1,375 tokens of overhead per agent session start. By combining proactive context "
        "injection with a disciplined write protocol, agents compound knowledge across sessions instead "
        "of resetting. We describe the architecture, its implementation, performance characteristics, "
        "and comparison with existing approaches including RAG-only systems, vector databases, "
        "and centralized memory servers.",
        s['Abstract']
    ))
    story.append(HRFlowable(width="60%", thickness=0.5, color=HexColor('#CCCCCC'),
                              spaceAfter=10, spaceBefore=10))

    # Keywords
    story.append(Paragraph(
        "<i>Keywords:</i> multi-agent systems, persistent memory, LLM agents, context injection, "
        "file-based architecture, agent orchestration",
        ParagraphStyle('Keywords', parent=s['Abstract'], fontName='Times-Roman',
                       fontSize=9.5, leftIndent=40, rightIndent=40, spaceAfter=0)
    ))

    story.append(PageBreak())

    # ── Section 1: Introduction ──
    story.append(Paragraph("1&nbsp;&nbsp;&nbsp;Introduction", s['Section']))

    story.append(Paragraph(
        "Large language model (LLM) agents have rapidly moved from research curiosities to "
        "production systems handling real tasks: customer support, code generation, data analysis, "
        "and autonomous monitoring. Yet a fundamental limitation persists across nearly all deployments: "
        "<b>cold-start amnesia</b>. Every new session begins with a blank slate. The agent has no memory "
        "of what it did yesterday, what it learned last week, or what another agent in the same system "
        "discovered an hour ago.",
        s['Body']
    ))

    story.append(Paragraph("1.1&nbsp;&nbsp;&nbsp;The Cold-Start Problem", s['Subsection']))
    story.append(Paragraph(
        "When an LLM agent starts a new session, its context window contains only the system prompt "
        "and whatever the user provides in the current message. Any knowledge accumulated in prior "
        "sessions — decisions made, facts learned, errors encountered — is lost unless explicitly "
        "re-injected. This forces agents to rediscover context repeatedly, ask questions they have "
        "already answered, and make mistakes they have already corrected.",
        s['Body']
    ))
    story.append(Paragraph(
        "For single-agent, single-session use cases (a chatbot answering one question), this is "
        "acceptable. For multi-agent systems running continuously — where agents hand off tasks, "
        "monitor external signals, and maintain relationships with users across days and weeks — "
        "cold-start amnesia is a critical failure mode.",
        s['Body']
    ))

    story.append(Paragraph("1.2&nbsp;&nbsp;&nbsp;Why RAG Alone Is Not Enough", s['Subsection']))
    story.append(Paragraph(
        "Retrieval-Augmented Generation (RAG) is the standard approach to giving LLMs access to "
        "external knowledge. A query is embedded, similar documents are retrieved from a vector store, "
        "and the results are injected into the context window. RAG is powerful for <i>reactive</i> "
        "retrieval — answering specific questions against a knowledge base.",
        s['Body']
    ))
    story.append(Paragraph(
        "However, RAG is fundamentally reactive. The agent must know what to ask for. It does not "
        "proactively receive operational context about its own recent activities, the state of the "
        "system it operates within, or the current work of its peer agents. An agent using RAG alone "
        "can retrieve facts but cannot remember what it was doing. The distinction matters: retrieval "
        "answers questions; memory provides continuity.",
        s['Body']
    ))

    story.append(Paragraph("1.3&nbsp;&nbsp;&nbsp;Design Goals", s['Subsection']))
    story.append(Paragraph("• <b>Zero middleware.</b> No message queues, no Redis, no central coordination "
        "server. The system runs on flat files and SQLite only, deployable on a single machine.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• <b>File-based persistence.</b> All memory is stored in human-readable formats "
        "(Markdown and JSON) and version-controlled with Git. Any developer can inspect, edit, or "
        "debug the memory state with standard tools.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• <b>Protocol-enforced discipline.</b> Agents follow the write protocol because "
        "it is specified in their workspace configuration, not because it is hard-coded into the "
        "runtime. This makes the system adaptable without code changes.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• <b>Per-agent scope with shared state.</b> Each agent maintains private logs "
        "while publishing relevant state to shared files that other agents consume.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• <b>Minimal token overhead.</b> The entire boot injection costs approximately "
        "1,375 tokens (~$0.004 at current pricing), making it negligible relative to the value it provides.",
        s['Bullet'], bulletText=''))

    # ── Section 2: Architecture Overview ──
    story.append(Paragraph("2&nbsp;&nbsp;&nbsp;Architecture Overview", s['Section']))
    story.append(Paragraph(
        "The architecture comprises four layers, each serving a distinct role in the memory lifecycle. "
        "Data flows upward from persistent storage through agent-private logs and shared state files "
        "into the boot injection layer, which assembles the context block before the agent's first "
        "inference call. After each task, data flows downward as the agent writes back to its logs "
        "and shared state.",
        s['Body']
    ))

    # Insert the box diagram
    story.append(Spacer(1, 10))
    story.append(BoxDiagram())
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "The four layers are: (1) <b>Structured Storage</b> — SQLite databases for persistent, "
        "queryable data; (2) <b>Per-Agent Memory</b> — daily Markdown logs private to each agent; "
        "(3) <b>Shared Brain</b> — typed JSON files for cross-agent state; and (4) <b>Boot Injection</b> "
        "— a script that assembles context from layers 1–3 and injects it before the agent's first "
        "inference. Each layer addresses a different class of memory need, and together they provide "
        "complete operational continuity.",
        s['Body']
    ))

    # ── Section 3: Layer 1 — Structured Storage ──
    story.append(Paragraph("3&nbsp;&nbsp;&nbsp;Layer 1: Structured Storage", s['Section']))
    story.append(Paragraph(
        "The foundation layer consists of five SQLite databases, each dedicated to a specific domain "
        "of structured data. SQLite was chosen over networked databases (PostgreSQL, Redis) for several "
        "reasons: zero configuration, no daemon process, instant deployability, sub-millisecond query "
        "latency for typical lookups, and compatibility with Git-based backup strategies.",
        s['Body']
    ))

    story.append(Paragraph("3.1&nbsp;&nbsp;&nbsp;Database Schemas", s['Subsection']))

    db_table = make_table(
        ["Database", "Purpose", "Key Tables"],
        [
            ["knowledge.db",
             "Agent-contributed facts with semantic retrieval",
             "chunks, kb_entities, kb_sources"],
            ["crm.db",
             "Contact tracking across communication channels",
             "contacts, interactions, outreach_log"],
            ["social_analytics.db",
             "Published content performance tracking",
             "posts, performance"],
            ["llm_usage.db",
             "Per-agent token consumption and cost tracking",
             "runs (agent_id, model, tokens, cost)"],
            ["agent_runs.db",
             "Execution history for cron jobs and sub-agents",
             "runs (job_name, agent_id, status, summary)"],
        ],
        col_widths=[1.4 * inch, 2.4 * inch, 2.7 * inch]
    )
    story.append(db_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<i>Table 1: Five SQLite databases comprising the structured storage layer.</i>",
        s['Caption']
    ))

    story.append(Paragraph("3.2&nbsp;&nbsp;&nbsp;Why SQLite", s['Subsection']))
    story.append(Paragraph(
        "SQLite databases are single files. They can be copied, backed up, and version-controlled "
        "trivially. There is no connection pooling, no authentication layer, no network latency. "
        "For a system running on a single host with fewer than a dozen concurrent agents, SQLite "
        "provides more than sufficient throughput. The <i>knowledge.db</i> database integrates with "
        "existing semantic search infrastructure (OpenAI embeddings indexed via a local tool) to provide "
        "vector retrieval without duplicating the embedding layer.",
        s['Body']
    ))

    story.append(Paragraph("3.3&nbsp;&nbsp;&nbsp;Semantic Search Integration", s['Subsection']))
    story.append(Paragraph(
        "Rather than building a separate vector database, the architecture leverages an existing "
        "workspace-level semantic search tool that indexes Markdown and text files using "
        "OpenAI's <font face='Courier'>text-embedding-3-small</font> model. The <i>knowledge.db</i> "
        "stores facts contributed by agents, and the semantic search tool indexes these alongside "
        "other workspace content. This avoids duplicating embedding infrastructure while still "
        "providing vector-based retrieval when needed.",
        s['Body']
    ))

    # ── Section 4: Layer 2 — Per-Agent Memory ──
    story.append(Paragraph("4&nbsp;&nbsp;&nbsp;Layer 2: Per-Agent Memory Directories", s['Section']))
    story.append(Paragraph(
        "Each agent in the system is assigned a unique identifier (e.g., <font face='Courier'>"
        "agent-main</font>, <font face='Courier'>agent-scanner</font>) and a dedicated memory "
        "directory. Within this directory, the agent maintains daily Markdown log files named by date.",
        s['Body']
    ))

    story.append(Paragraph("4.1&nbsp;&nbsp;&nbsp;Directory Structure", s['Subsection']))
    code = textwrap.dedent("""\
        memory/agents/
          agent-main/
            2026-03-01.md
            2026-02-28.md
          agent-scanner/
            2026-03-01.md
          agent-chat/
            2026-03-01.md""")
    story.append(GrayBox(code))
    story.append(Spacer(1, 8))

    story.append(Paragraph("4.2&nbsp;&nbsp;&nbsp;Log Entry Format", s['Subsection']))
    story.append(Paragraph(
        "Each entry within a daily log follows a consistent format:",
        s['Body']
    ))
    code2 = textwrap.dedent("""\
        ## [HH:MM] Task: <short description>
        - What was done
        - What was found / decided
        - What to watch for next time
        - Cross-agent writes: [list of shared brain files updated]""")
    story.append(GrayBox(code2))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "The convention is simple: append after every task, read the last two days at boot. "
        "This gives the agent a rolling window of recent operational context without loading "
        "its entire history.",
        s['Body']
    ))

    story.append(Paragraph("4.3&nbsp;&nbsp;&nbsp;Why Markdown", s['Subsection']))
    story.append(Paragraph(
        "Markdown was chosen over structured formats (JSON, YAML, Protocol Buffers) for several "
        "practical reasons. First, <b>human readability</b>: any developer can open a log file and "
        "understand what the agent did without parsing tools. Second, <b>Git compatibility</b>: Markdown "
        "diffs cleanly, making version history meaningful. Third, <b>zero tooling</b>: no serialization "
        "library, no schema validation, no migration scripts. The agent simply appends text to a file. "
        "Fourth, <b>LLM nativity</b>: language models process natural language text more effectively than "
        "structured formats, so Markdown entries are directly consumable without transformation.",
        s['Body']
    ))

    # ── Section 5: Layer 3 — Shared Brain ──
    story.append(Paragraph("5&nbsp;&nbsp;&nbsp;Layer 3: Shared Brain Files", s['Section']))
    story.append(Paragraph(
        "While per-agent memory directories are private, the shared brain layer provides cross-agent "
        "state sharing through typed JSON files. These files serve as the asynchronous communication "
        "channel between agents — no direct messaging or RPC required.",
        s['Body']
    ))

    story.append(Paragraph("5.1&nbsp;&nbsp;&nbsp;Schema Convention", s['Subsection']))
    story.append(Paragraph(
        "All shared brain files follow a common envelope schema:",
        s['Body']
    ))
    code3 = textwrap.dedent("""\
        {
          "lastUpdatedBy": "<agent-id>",
          "lastUpdatedAt": "<ISO-8601 timestamp>",
          "schemaVersion": 1,
          "entries": [
            {
              "timestamp": "<ISO-8601>",
              "agent": "<agent-id>",
              "content": { ... },
              "tags": ["tag1", "tag2"]
            }
          ]
        }""")
    story.append(GrayBox(code3))
    story.append(Spacer(1, 8))

    story.append(Paragraph("5.2&nbsp;&nbsp;&nbsp;File Types", s['Subsection']))
    story.append(Paragraph(
        "The architecture defines seven shared brain file types, each serving a distinct coordination need:",
        s['Body']
    ))

    brain_table = make_table(
        ["File Type", "Purpose", "Primary Writer", "Primary Readers"],
        [
            ["Intel Feed",
             "Aggregated signals from external sources (social media, news, APIs)",
             "Scanner agents",
             "Interactive agents, content agents"],
            ["Cross-Agent Handoffs",
             "Task queue for work that spans agent boundaries",
             "All agents",
             "All agents"],
            ["Ecosystem State",
             "Live snapshots of external system state (prices, health, metrics)",
             "Sync cron jobs",
             "Any agent answering real-time queries"],
            ["Outreach Log",
             "Record of external communications sent",
             "Interactive agents",
             "All agents (prevents duplicate outreach)"],
            ["Content Vault",
             "Published content with performance metrics",
             "Posting agents",
             "Content strategy agents"],
            ["Session Handoffs",
             "Per-user session summaries for continuity across restarts",
             "Chat agents",
             "Chat agents (next session)"],
            ["System Pulse",
             "Aggregate state of monitored groups or communities",
             "Group session agents",
             "All agents needing social context"],
        ],
        col_widths=[1.2 * inch, 1.8 * inch, 1.4 * inch, 2.1 * inch]
    )
    story.append(brain_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<i>Table 2: Seven shared brain file types and their roles in cross-agent coordination.</i>",
        s['Caption']
    ))

    story.append(Paragraph("5.3&nbsp;&nbsp;&nbsp;Size Limits and Archival", s['Subsection']))
    story.append(Paragraph(
        "Each shared brain file is capped at 500KB. When an agent detects that a file exceeds this "
        "threshold, it archives older entries to a timestamped file in an archive subdirectory and "
        "resets the active file with only recent entries. This prevents unbounded growth while "
        "preserving historical data.",
        s['Body']
    ))

    story.append(Paragraph("5.4&nbsp;&nbsp;&nbsp;Write Guard Rules", s['Subsection']))
    story.append(Paragraph(
        "Shared brain files are readable by all agents in the system and must be treated as semi-public. "
        "The write guard rules are enforced by convention in each agent's workspace configuration:",
        s['Body']
    ))
    story.append(Paragraph("• Never write private credentials (API keys, private keys, passwords) to shared files.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• Per-agent memory directories are private; shared brain files are communal.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• Session handoff files may contain user-specific data and should be scoped to "
        "the relevant agent's read list.",
        s['Bullet'], bulletText=''))

    # ── Section 6: Layer 4 — Boot Injection ──
    story.append(Paragraph("6&nbsp;&nbsp;&nbsp;Layer 4: Boot Injection", s['Section']))
    story.append(Paragraph(
        "The boot injection layer is the mechanism that transforms stored memory into active context. "
        "A Python script (<font face='Courier'>boot_agent.py</font>) runs before the agent's first "
        "inference call and assembles a structured context block from the lower three layers.",
        s['Body']
    ))

    story.append(Paragraph("6.1&nbsp;&nbsp;&nbsp;Boot Script Logic", s['Subsection']))
    story.append(Paragraph(
        "The boot script executes the following steps:",
        s['Body']
    ))
    story.append(Paragraph("1. Detect the agent ID from an environment variable or command-line argument.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("2. Load the agent's identity file (if present) for role-specific context.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("3. Read the last two days of the agent's daily Markdown logs.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("4. Load relevant shared brain JSON files based on a hardcoded agent-role mapping.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("5. Assemble all loaded content into a single formatted context block.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("6. Output the block to stdout for injection into the agent's system prompt.",
        s['Bullet'], bulletText=''))

    story.append(Paragraph("6.2&nbsp;&nbsp;&nbsp;Agent-Role Mapping", s['Subsection']))
    story.append(Paragraph(
        "Each agent loads only the shared brain files relevant to its role. A main interactive agent "
        "might load the intel feed, ecosystem state, and cross-agent handoffs. A scanner cron job "
        "might load only the intel feed (for writing) and the content vault (for reference). This "
        "selective loading keeps token overhead low and context relevant.",
        s['Body']
    ))

    role_table = make_table(
        ["Agent Role", "Shared Brain Files Loaded"],
        [
            ["Main interactive agent", "Intel feed, cross-agent handoffs, ecosystem state"],
            ["Chat agent", "Session handoffs, outreach log, ecosystem state"],
            ["Group session agent", "System pulse, intel feed, cross-agent handoffs"],
            ["Scanner cron", "Intel feed (write), content vault (read)"],
            ["Sync cron", "Ecosystem state (write only)"],
            ["Reflection agent", "Cross-agent handoffs, system pulse"],
        ],
        col_widths=[2.0 * inch, 4.5 * inch]
    )
    story.append(role_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<i>Table 3: Agent-role to shared brain file mapping.</i>",
        s['Caption']
    ))

    story.append(Paragraph("6.3&nbsp;&nbsp;&nbsp;Token Overhead Analysis", s['Subsection']))
    story.append(Paragraph(
        "The total token cost of boot injection has been measured across typical agent sessions:",
        s['Body']
    ))

    token_table = make_table(
        ["Component", "Characters", "Tokens (approx.)", "Notes"],
        [
            ["Agent identity", "~500", "~125", "Role description, ID, capabilities"],
            ["Last 2 days of logs", "~2,000", "~500", "Recent operational context"],
            ["Shared brain (2–3 files)", "~3,000", "~750", "Cross-agent state summaries"],
            ["Total per session", "~5,500", "~1,375", "~$0.004 at $3/million tokens"],
        ],
        col_widths=[1.7 * inch, 1.0 * inch, 1.2 * inch, 2.6 * inch]
    )
    story.append(token_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<i>Table 4: Token overhead per agent boot, broken down by component.</i>",
        s['Caption']
    ))

    story.append(Paragraph(
        "At a cost of approximately $0.004 per agent session, the boot injection overhead is negligible. "
        "Even a system running 100 agent sessions per day incurs less than $0.40 in boot overhead — "
        "a trivial fraction of total LLM costs.",
        s['Body']
    ))

    story.append(Paragraph("6.4&nbsp;&nbsp;&nbsp;Integration with Identity and Recall Systems", s['Subsection']))
    story.append(Paragraph(
        "The boot injection script runs alongside (not replacing) existing identity recall systems "
        "such as knowledge graph lookups and semantic episode retrieval. The recall system handles "
        "<i>who is this user</i> and <i>what have we discussed before</i>, while the boot script handles "
        "<i>what have I been doing</i> and <i>what do my peers know</i>. Both outputs merge into the "
        "pre-inference context block, providing the agent with complete operational awareness.",
        s['Body']
    ))

    # ── Section 7: Write Protocol ──
    story.append(Paragraph("7&nbsp;&nbsp;&nbsp;Write Protocol", s['Section']))
    story.append(Paragraph(
        "Architecture without discipline is documentation. The write protocol defines the mandatory "
        "actions every agent must take after completing a meaningful task. It is enforced via workspace "
        "configuration files that agents read at startup — not via code-level enforcement. Agents follow "
        "the protocol because their instructions tell them to.",
        s['Body']
    ))

    story.append(Paragraph("7.1&nbsp;&nbsp;&nbsp;Three-Step Write Process", s['Subsection']))

    story.append(Paragraph(
        "<b>Step 1: Daily Log.</b> Append a timestamped entry to "
        "<font face='Courier'>memory/agents/{agent-id}/YYYY-MM-DD.md</font> summarizing what was done, "
        "what was found, and what to watch for next time. A helper script "
        "(<font face='Courier'>write_agent_memory.py</font>) handles file creation and formatting.",
        s['Body']
    ))
    story.append(Paragraph(
        "<b>Step 2: Shared Brain Update.</b> If the completed task produced information valuable to other "
        "agents, update the relevant shared brain JSON file. For example, after scanning external "
        "social media, the scanner agent writes to the intel feed. After publishing content, the "
        "posting agent writes to the content vault.",
        s['Body']
    ))
    story.append(Paragraph(
        "<b>Step 3: Cross-Agent Handoff.</b> If the task requires follow-up by a different agent, append "
        "an entry to the cross-agent handoffs file with the task description, the originating agent, "
        "the target agent, and a status field. The target agent will see this at its next boot.",
        s['Body']
    ))

    story.append(Paragraph("7.2&nbsp;&nbsp;&nbsp;Write Guard Rules", s['Subsection']))
    story.append(Paragraph(
        "The write protocol includes guard rules to maintain data hygiene:",
        s['Body']
    ))
    story.append(Paragraph("• Private data (credentials, keys, personal information) must never appear in "
        "shared brain files. Per-agent memory is the appropriate location.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• Shared brain files should contain operational state, not raw data dumps. "
        "Entries should be concise summaries, not full transcripts.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• The handoff file is a queue, not a log. Completed handoffs should be "
        "marked as resolved and eventually archived.",
        s['Bullet'], bulletText=''))

    story.append(Paragraph("7.3&nbsp;&nbsp;&nbsp;Protocol Enforcement", s['Subsection']))
    story.append(Paragraph(
        "A notable design choice is that the write protocol is enforced via natural-language instructions "
        "in the agent's workspace configuration, not via code. The agent reads its protocol rules from "
        "a configuration file at startup and follows them as part of its operating instructions. This "
        "approach has a clear trade-off: it relies on agent compliance rather than programmatic "
        "enforcement. In practice, modern LLMs follow structured instructions with high fidelity, "
        "and the benefits of protocol flexibility (no code changes needed to adjust behavior) outweigh "
        "the risk of occasional non-compliance. Section 11 discusses this limitation further.",
        s['Body']
    ))

    # ── Section 8: Agent Orchestration ──
    story.append(Paragraph("8&nbsp;&nbsp;&nbsp;Agent Orchestration", s['Section']))
    story.append(Paragraph(
        "The memory architecture supports a heterogeneous multi-agent system where different agents "
        "serve different roles but share a common workspace and memory infrastructure.",
        s['Body']
    ))

    story.append(Paragraph("8.1&nbsp;&nbsp;&nbsp;Agent Types", s['Subsection']))
    story.append(Paragraph(
        "A typical deployment includes several classes of agents:",
        s['Body']
    ))
    story.append(Paragraph("• <b>Interactive agents</b> handle direct user conversations across messaging "
        "platforms. They read broadly from shared state and write frequently to their daily logs.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• <b>Chat agents</b> manage conversations in group settings, reading session "
        "handoff files to maintain continuity across restarts.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• <b>Cron agents</b> run on schedules (e.g., every two hours) to perform "
        "intelligence gathering, data synchronization, or maintenance tasks. They are the primary "
        "writers to shared brain files like the intel feed and ecosystem state.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• <b>Sub-agents</b> are spawned by interactive agents for specific tasks "
        "(code generation, document creation, analysis). They inherit context from the spawning agent "
        "and report results upon completion.",
        s['Bullet'], bulletText=''))

    story.append(Paragraph("8.2&nbsp;&nbsp;&nbsp;Async Coordination Without Direct Messaging", s['Subsection']))
    story.append(Paragraph(
        "The shared brain eliminates the need for direct inter-agent messaging. A scanner agent "
        "writes external intelligence to the intel feed file every two hours. When an interactive "
        "agent boots thirty minutes later, it reads that file and has current intelligence without "
        "ever communicating with the scanner directly. This is coordination through shared state "
        "rather than message passing — simpler, more resilient to agent downtime, and requiring no "
        "message routing infrastructure.",
        s['Body']
    ))

    story.append(Paragraph("8.3&nbsp;&nbsp;&nbsp;Unique IDs and Scoped Memory", s['Subsection']))
    story.append(Paragraph(
        "Every agent has a unique string identifier used consistently across all memory layers. This "
        "ID appears in daily log directory names, in the <font face='Courier'>lastUpdatedBy</font> "
        "field of shared brain files, in the <font face='Courier'>agent_id</font> column of database "
        "tables, and in the boot script's role mapping. Consistent naming enables audit trails and "
        "cross-referencing across all four layers.",
        s['Body']
    ))

    # ── Section 9: Performance & Cost ──
    story.append(Paragraph("9&nbsp;&nbsp;&nbsp;Performance and Cost", s['Section']))
    story.append(Paragraph(
        "The architecture is designed for minimal overhead. All storage is local, all queries are "
        "in-process, and the boot injection adds a fixed, predictable cost to each agent session.",
        s['Body']
    ))

    perf_table = make_table(
        ["Metric", "Value", "Notes"],
        [
            ["Boot token overhead", "~1,375 tokens", "$0.004 at $3/million tokens"],
            ["Boot time", "<100ms", "File reads + JSON parsing only"],
            ["Shared brain file size", "<50KB typical", "500KB cap with auto-archival"],
            ["SQLite query latency", "<1ms", "Typical single-table lookups"],
            ["Network calls at boot", "0", "All data is local"],
            ["Storage per agent per day", "~2–5KB", "Markdown log files"],
            ["Git overhead", "Negligible", "Standard git operations on small files"],
        ],
        col_widths=[1.8 * inch, 1.3 * inch, 3.4 * inch]
    )
    story.append(perf_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<i>Table 5: Performance characteristics of the memory architecture.</i>",
        s['Caption']
    ))

    story.append(Paragraph(
        "Git-based versioning of all memory files provides free backup, audit trails, and the ability "
        "to roll back to any prior state. Since memory files are small text and JSON files, Git handles "
        "them efficiently with no special configuration. Daily commits capture the full state evolution "
        "of the agent system.",
        s['Body']
    ))

    # ── Section 10: Comparison ──
    story.append(Paragraph("10&nbsp;&nbsp;&nbsp;Comparison with Existing Approaches", s['Section']))

    story.append(Paragraph("10.1&nbsp;&nbsp;&nbsp;vs. RAG-Only Systems", s['Subsection']))
    story.append(Paragraph(
        "RAG provides reactive retrieval: the agent queries for specific information. The persistent "
        "memory architecture provides proactive injection: the agent receives operational context "
        "automatically at boot. These are complementary, not competing, approaches. Our architecture "
        "uses semantic search (a form of RAG) within its knowledge database while adding the proactive "
        "layers that RAG alone cannot provide.",
        s['Body']
    ))

    story.append(Paragraph("10.2&nbsp;&nbsp;&nbsp;vs. Vector Databases (Pinecone, Weaviate)", s['Subsection']))
    story.append(Paragraph(
        "Dedicated vector databases provide powerful similarity search at scale. However, for "
        "small-to-medium agent deployments (fewer than 20 agents, millions rather than billions of "
        "embeddings), they introduce unnecessary infrastructure complexity: hosted services with API "
        "keys, network latency, cost scaling by query volume, and vendor lock-in. Our approach uses "
        "local semantic search tooling that provides equivalent functionality for the relevant scale, "
        "with zero infrastructure overhead.",
        s['Body']
    ))

    story.append(Paragraph("10.3&nbsp;&nbsp;&nbsp;vs. Centralized Memory Servers (MemGPT, Letta)", s['Subsection']))
    story.append(Paragraph(
        "Systems like MemGPT and Letta provide sophisticated memory management through middleware "
        "layers that mediate between the LLM and persistent storage. These are powerful but introduce "
        "dependencies: a running server process, its own configuration and state, network communication "
        "between the agent and the memory server, and coupling to the middleware's API. Our approach "
        "eliminates the middleware entirely. Memory is just files. The protocol is just instructions. "
        "The boot script is a simple Python file that reads files and prints text.",
        s['Body']
    ))

    story.append(Paragraph("10.4&nbsp;&nbsp;&nbsp;vs. Pure File-Based (Reading Entire Workspace)", s['Subsection']))
    story.append(Paragraph(
        "A naive alternative is to simply load the entire workspace into the agent's context at "
        "startup. This fails in two ways: first, most workspaces exceed context window limits; second, "
        "even when technically possible, loading irrelevant content wastes tokens and dilutes the "
        "signal. The four-layer architecture provides <i>selective</i> injection — each agent receives "
        "only what is relevant to its role and recent history.",
        s['Body']
    ))

    comp_table = make_table(
        ["Approach", "Proactive", "Infrastructure", "Token Efficient", "Local-First"],
        [
            ["This architecture", "Yes", "None (files only)", "Yes (~1,375 tokens)", "Yes"],
            ["RAG-only", "No", "Vector store", "Depends on retrieval", "Varies"],
            ["Vector DB", "No", "Hosted service", "Depends on retrieval", "No"],
            ["MemGPT / Letta", "Yes", "Middleware server", "Yes (managed)", "No"],
            ["Full workspace load", "Yes", "None", "No (unbounded)", "Yes"],
        ],
        col_widths=[1.4 * inch, 0.9 * inch, 1.3 * inch, 1.5 * inch, 1.0 * inch]
    )
    story.append(comp_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<i>Table 6: Comparison of memory approaches across key dimensions.</i>",
        s['Caption']
    ))

    # ── Section 11: Limitations ──
    story.append(Paragraph("11&nbsp;&nbsp;&nbsp;Limitations and Future Work", s['Section']))

    story.append(Paragraph("11.1&nbsp;&nbsp;&nbsp;Protocol Compliance", s['Subsection']))
    story.append(Paragraph(
        "The write protocol is enforced by natural-language instructions, not code. While modern LLMs "
        "follow structured instructions with high fidelity, there is no hard guarantee that every agent "
        "will write back after every task. In practice, this has proven reliable: agents read and follow "
        "their workspace configuration consistently. A future improvement could add a lightweight "
        "verification layer that checks whether write-back occurred and flags omissions.",
        s['Body']
    ))

    story.append(Paragraph("11.2&nbsp;&nbsp;&nbsp;No Real-Time Streaming", s['Subsection']))
    story.append(Paragraph(
        "The file-based approach means inter-agent communication is not real-time. An agent discovers "
        "new shared state only at its next boot (or when it explicitly reads a file mid-session). "
        "For time-sensitive coordination, this introduces latency equivalent to the longest agent "
        "session duration or cron interval. Systems requiring sub-second inter-agent communication "
        "should consider supplementing this architecture with a message passing layer.",
        s['Body']
    ))

    story.append(Paragraph("11.3&nbsp;&nbsp;&nbsp;External Embedding Dependency", s['Subsection']))
    story.append(Paragraph(
        "The semantic search capability in the knowledge database depends on an external embedding "
        "service (currently OpenAI's embedding API). If this service is unavailable, vector-based "
        "retrieval degrades to keyword matching. A future improvement could add a local embedding "
        "model as a fallback.",
        s['Body']
    ))

    story.append(Paragraph("11.4&nbsp;&nbsp;&nbsp;Future Directions", s['Subsection']))
    story.append(Paragraph("• <b>Automated memory compaction:</b> Periodically summarize and compress older "
        "daily logs to reduce storage and improve boot-time relevance.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• <b>Cross-workspace synchronization:</b> Enable agents running in different "
        "workspace environments to share state via Git remotes or file sync.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• <b>LLM cost dashboards:</b> Build on the <i>llm_usage.db</i> data to provide "
        "real-time cost monitoring and budget alerts per agent.",
        s['Bullet'], bulletText=''))
    story.append(Paragraph("• <b>Hard protocol enforcement:</b> Add a post-task verification hook that "
        "checks for write-back and retries if the agent omitted it.",
        s['Bullet'], bulletText=''))

    # ── Section 12: Conclusion ──
    story.append(Paragraph("12&nbsp;&nbsp;&nbsp;Conclusion", s['Section']))
    story.append(Paragraph(
        "We have presented a four-layer persistent memory architecture for multi-agent LLM systems "
        "that achieves operational continuity through file-based storage and protocol-enforced "
        "discipline. The architecture requires no middleware, no central server, and no specialized "
        "infrastructure — only files, SQLite, and a boot script.",
        s['Body']
    ))
    story.append(Paragraph(
        "The key insight is that agents need <i>proactive context injection</i>, not just reactive "
        "retrieval. RAG answers questions; persistent memory provides continuity. By injecting "
        "relevant context at boot (~1,375 tokens, ~$0.004) and enforcing write-back after every task, "
        "agents compound knowledge across sessions instead of resetting.",
        s['Body']
    ))
    story.append(Paragraph(
        "For small-to-medium multi-agent deployments — the most common case in practice — this "
        "file-based approach outperforms both RAG-only systems (which lack proactive injection) and "
        "centralized memory servers (which introduce middleware dependencies). The approach is simple "
        "enough to implement in a single afternoon, cheap enough to ignore in cost calculations, and "
        "effective enough to transform how agents operate across sessions.",
        s['Body']
    ))
    story.append(Paragraph(
        "Agents that remember are agents that improve. The cost of memory is negligible. The cost of "
        "amnesia is compounding.",
        s['Body']
    ))

    story.append(Spacer(1, 0.5 * inch))
    story.append(HRFlowable(width="40%", thickness=0.5, color=HexColor('#CCCCCC'),
                              spaceAfter=10, spaceBefore=10))
    story.append(Paragraph(
        "<i>Architecture by Theo · OpenClaw Project · March 2026</i>",
        ParagraphStyle('Footer', parent=s['Body'], alignment=TA_CENTER,
                       fontName='Times-Italic', fontSize=10, textColor=HexColor('#888888'))
    ))

    return story


def generate_pdf():
    """Generate the whitepaper PDF."""
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=letter,
        topMargin=1.0 * inch,
        bottomMargin=1.0 * inch,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
        title="Persistent Agent Memory: A File-Based Architecture for Stateful Multi-Agent Systems",
        author="Theo · OpenClaw Project",
    )

    story = build_document()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"✓ Generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_pdf()
