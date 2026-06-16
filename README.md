# Bookly Support Agent

A conversational customer support agent for Bookly, a fictional online bookstore. Built with Python and the Anthropic API.

The agent handles order status inquiries, returns and refunds, order cancellations and modifications, shipping questions, and general policy questions. It uses Claude's tool-calling capability to look up order data and enforce business rules, and escalates to a human agent when something falls outside its scope.

## How to run it

**1. Clone the repo**
```
git clone <your-repo-url>
cd bookly-agent
```

**2. Install dependencies**
```
pip install -r requirements.txt
```

**3. Set your Anthropic API key**
```
export ANTHROPIC_API_KEY="your-key-here"
```

**4. Run the agent**
```
python agent.py
```

Type your message and press enter. Type `quit` or `exit` to end the session.

## Project structure

- `agent.py` — the main conversation loop, system prompt, and Anthropic API calls
- `tools.py` — mock order database, FAQ knowledge base, tool functions, and tool schemas

## Sample order IDs to test with

- `ORD-001` — Processing (eligible for cancellation)
- `ORD-002` — Shipped (has tracking number)
- `ORD-003` — Delivered, within 30-day return window
- `ORD-004` — Delivered, outside 30-day return window
- `ORD-005` — Delivered, but marked Final Sale (non-returnable)

## Architecture notes

The agent is built around three deliberate design choices:

**Policy rules live in code, not just the prompt.** Hard constraints like the 30-day return window, final sale ineligibility, and shipped-order locks are enforced inside the tool functions in `tools.py`. The code gives the same answer every time regardless of how the conversation goes. The system prompt governs tone, sequencing, and judgment calls — things that benefit from flexibility.

**Confirm before acting.** The agent shows a summary and asks for explicit confirmation before any return or cancellation executes. It also re-fetches order details right before the confirmation step so the summary reflects current data, not something from earlier in the conversation.

**Escalation creates a real ticket.** The `escalate_to_human` tool returns a ticket ID rather than just a verbal promise. Damage claims, out-of-scope requests, and frustrated customers all route through this tool so escalations are trackable rather than just acknowledged.


## What I'd do differently with more time

- Replace the hardcoded FAQ dictionary with retrieval over real help center documents so policy answers are always current
- Add persistent conversation logging so sessions can be reviewed after the fact
- Add error handling and retry logic around the Anthropic API call for production resilience
- Add an intent classification step if the scope grew beyond four or five use cases, to keep each domain prompt focused
