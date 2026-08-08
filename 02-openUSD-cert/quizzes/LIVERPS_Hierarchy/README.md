# LIVERPS + Hierarchy Behavior





Before you can use any rule below, you have to answer ONE question first: **are we talking
about ONE prim, or TWO prims (a parent and a child)?** That single question decides which
whole rulebook you reach for.

| | Same prim | Parent + Child (two prims) |
|---|---|---|
| **What's actually happening** | **LIVERPS**: one prim, with multiple opinions about that same attribute, arriving through different arcs | **Hierarchy**: two prims, each with their own opinion about the same-named attribute |
| **What you're solving for** | Picking the single **winning value** on one prim — "which opinion wins?" | Tracing how the **innermost (child) prim** ends up affected by what its ancestors authored above it — "how does the value coming down from above affect this specific descendant?" The parent's own value is never in question; only the child's resolved outcome is |
| **Which rulebook applies** | **LIVERPS** — strict strength ordering, exactly ONE opinion wins outright | **Hierarchy behavior** — depends on the attribute type (A/B/C/D/E below); sometimes the child wins, sometimes values combine, sometimes there's no relationship at all |
| **How to spot it** | Every opinion mentioned targets the exact same path, e.g. `/Ball` | One opinion targets `/World`, another targets `/World/Ball` — a nested path |

### Build the intuition with one example, run both ways

**LIVERPS version** — everything is about the SAME prim, `/Ball`:
```
/Ball → local opinion: displayColor = green
/Ball → payload also contributes: displayColor = blue
```
Only one wins: **green**, because Local outranks Payload. Nothing "combines."

**Hierarchy version** — now it's TWO prims, `/World` and its child `/World/Ball`:
```
/World       → local opinion: displayColor = green
/World/Ball  → its own opinion (via payload): displayColor = blue
```
`/World` stays green. `/World/Ball` is blue. **Both are true at once** — they're two different
prims, not two opinions competing over one prim. This is Type A hierarchy behavior, not LIVERPS.

**The exact same-looking words ("green," "blue," "payload") produce a totally different kind of
answer depending on whether one path or two paths are involved. Always count the prims first.**

---

## HIERARCHY BEHAVIOR: what "child wins" or "parent wins" actually means

This is the single most important thing to get right, and it's easy to misread every table
below without it.

- **"Child wins" does NOT mean the child's value replaces or overwrites the parent's value
  anywhere.** Each prim ALWAYS keeps its own authored value, unchanged, forever.
- **"Wins" only describes the answer to one specific question**: "when someone asks THIS ONE
  PRIM what its value is, which number does it report back?"
- **There is no single global answer for the whole scene.** Every prim gets asked separately,
  and every prim can report back a different answer.

### Worked example — primvars (Type A)

```
/parent   → authors displayColor = red
/parent/child → authors NOTHING for displayColor
```

- Ask `/parent` "what's your color?" → **red** (its own authored value)
- Ask `/parent/child` "what's your color?" → **red** (it has nothing of its own, so it reports
  its parent's value as a fallback)

Now change it so the child DOES author its own value:
```
/parent   → authors displayColor = red
/parent/child → authors displayColor = blue
```

- Ask `/parent` "what's your color?" → **still red** — completely unaffected, nothing changed
  here at all
- Ask `/parent/child` "what's your color?" → **blue** — its own value

**"Child wins" here just means: `/parent/child`, when asked, reports blue instead of falling
back to red. `/parent` was never touched, never overwritten, never asked to change anything.**

### Worked example — transforms (Type C)

```
/parent        → local translate = 10
/parent/child  → local translate = 15
```

- `/parent`'s own LOCAL value → **10**, always, unchanged
- `/parent/child`'s own LOCAL value → **15**, always, unchanged
- `/parent`'s WORLD-SPACE position (computed) → **10** (nothing above it to combine with)
- `/parent/child`'s WORLD-SPACE position (computed) → **10 + 15 = 25**

**The "25" isn't stored anywhere on either prim:**
- It's not a value that exists on `/parent`, and it's not `/parent/child`'s local attribute
  either.
- It's the **ANSWER** to a specific computed question — "where is `/parent/child` actually
  located in the world?" — worked out by walking up the hierarchy and combining every
  ancestor's local value with this prim's own local value.
- Ask that same question about `/parent`, and the answer is just 10, since there's nothing
  above it to add in.

### The one rule to hold onto for every table below

- **Every row in every table describes the answer for ONE SPECIFIC PRIM being asked about its
  own value.**
- **"Child wins"** = when you ask the CHILD specifically, you get the child's number.
- **"Parent wins"** (Type B, E) = when you ask the CHILD specifically, you get the PARENT's
  number instead of the child's own — but the parent's own answer, when you ask the parent
  directly, never changes either way.
- **Nothing is ever being overwritten** in the actual authored data — every prim's own
  authored opinion sits exactly where you put it, permanently. "Winning" only decides what
  gets reported back when a specific prim is queried.
- **Transforms produce a THIRD kind of answer** (world-space position) that isn't stored on
  either prim at all — it's computed fresh, on demand, by combining both.

---

## HIERARCHY MODES: The Legend of 5 Types of Behavior

| Type | Plain description |
|---|---|
| **Type A** | Child wins if it has its own value. If the child has no value, it uses the parent's value instead. |
| **Type B** | If the parent is "off," the child is forced "off" too, no matter what the child says. The child CAN turn itself off on its own, but the child can never turn itself back "on" if the parent already said off. |
| **Type C** | Parent and child values are always combined together mathematically. Neither one "wins" — both are always used. |
| **Type D** | Parent and child have completely no relationship. The child never looks at the parent at all, even if the child has nothing set. |
| **Type E** | Normally behaves like Type A (child wins if set), but there's a switch you can flip to force the parent to win instead. The only type where the rule itself is configurable. |

---

## Which attribute uses which type

| Attribute | Type |
|---|---|
| Primvars (`displayColor`, `width`, `roughness`, any custom primvar) | **A** |
| Purpose (`render`/`proxy`/`guide`) | **A** |
| `model:drawMode` (bounding box vs. full geometry draw mode) | **A** |
| Visibility | **B** |
| Active / Inactive | **B** (stricter version — see note below) |
| Transforms (translate/rotate/scale) | **C** |
| Skeleton joint transforms (`UsdSkel`) | **C** |
| Point instancer prototype transforms | **C** |
| Kind (component/group/assembly) | **D** |
| Ordinary attributes (radius, mass, any plain schema attribute) | **D** |
| Relationships in general (`proxyPrim`, a relationship's target list) | **D** |
| Extent / bounding box | **D** |
| Material binding (`material:binding`) | **E** |

**Note on Active/Inactive vs. Visibility (both Type B)**: with Visibility, the child still
technically exists, it's just not drawn. With Active/Inactive, if the parent is off, the child
doesn't exist at all — it's completely erased, so there's nothing left to even check the
child's own opinion on.

**Note on relationships (Type D)**: a child never "inherits" a relationship target from its
parent — each prim's relationships are entirely its own. Separately, relationships DO get
automatically re-targeted when an asset is referenced elsewhere — but that's a totally
different mechanism (path remapping across composition arcs), not hierarchy inheritance.
Don't mix the two up.

---

## Type A — with numbers

Applies to: Primvars, Purpose, `model:drawMode`.

| Parent's number | Child's own number | What you get if you ask the CHILD |
|---|---|---|
| 0.8 | (nothing set) | **0.8** (takes parent's number) |
| 0.8 | 0.3 | **0.3** (child's own number wins) |
| (nothing set) | 0.3 | **0.3** (child's own number) |
| (nothing set) | (nothing set) | Falls back to the schema's built-in default number |

**How it works with numbers**: it's a simple swap, never math. The child either uses its own
number, or borrows the parent's number completely. Numbers are never added, multiplied, or
blended together.

---

## Type B — with numbers

Applies to: Visibility, Active/Inactive.

There ARE no numbers here — this type only applies to on/off style values (visible/invisible,
active/inactive), not numeric attributes. Skip the "numeric" question for this type — it
doesn't have one. Also worth knowing: these two are really the main Type B examples you'll be
asked about — there isn't a large family of these in core USD.

| Parent says | Child says | What you get if you ask the CHILD |
|---|---|---|
| On | On | On |
| On | Off | Off (child turned itself off) |
| Off | On | **Off** (parent wins, child cannot undo it) |
| Off | Off | Off |

---

## Type C — with numbers

Applies to: Transforms, Skeleton joint transforms, Point instancer prototype transforms.

This is the ONLY type where actual math happens. But the math is different depending on
which kind of transform value it is:

| Transform type | How parent + child combine |
|---|---|
| **Translate** (position) | **Added together** — parent +1 and child -1 → result 0 |
| **Scale** | **Multiplied together** — parent scale 2 and child scale 3 → result 6 |
| **Rotate** | **Combined in sequence** (like stacking two turns one after another) — not simple addition, but conceptually "both are applied, one after the other" |

| Parent's translate | Child's translate | Child's WORLD position (not stored anywhere, computed) |
|---|---|---|
| +1 | -1 | **0** |
| +1 | (nothing set) | **+1** (child contributes nothing, parent's number passes through) |
| (nothing set) | -1 | **-1** (parent contributes nothing, child's number stands alone) |
| (nothing set) | (nothing set) | 0 (no transform anywhere) |

**How it works with numbers**: unlike Type A, numbers here are never "picked" — they're always
mathematically combined. Even if a child sets nothing, that's treated as a neutral number
(0 for translate, 1 for scale) that still gets combined in, it just doesn't change the result.

**Skeleton joints and point instancer prototypes work the same way**: a joint's world
transform is the product of every parent joint's transform up the skeleton chain, and an
instance's transform composes with the instancer's own transform, using this exact same
multiplicative logic.

---

## Type D — with numbers

Applies to: Kind, ordinary attributes (radius, mass, etc.), relationships, extent.

| Parent's number | Child's own number | What you get if you ask the CHILD |
|---|---|---|
| 5.0 | 2.0 | **2.0** (its own number, unrelated to parent) |
| 5.0 | (nothing set) | **Schema's built-in default** (e.g. 1.0) — NOT 5.0, parent is never even checked |
| (nothing set) | 2.0 | **2.0** (its own) |
| (nothing set) | (nothing set) | Schema's built-in default |

**How it works with numbers**: the parent's number is invisible to the child. Even in the
"child has nothing set" row, the child does NOT borrow the parent's number — it falls back to
a hardcoded default built into the schema itself, completely independent of the parent.

**Relationships and extent aren't numeric in the same sense** (relationships point at other
prims; extent is a computed bounding box), but they follow this exact same "no relationship
at all" logic — the child never looks at what its parent authored.

---

## Type E — the one flippable type (Material Binding Strength)

There's one behavior that's genuinely different from all the others: **a case where you get to
CHOOSE whether the child or the parent wins**, instead of it being fixed.

**Material binding** (`material:binding`) works like Type A by default — a mesh's own local
material binding beats one inherited from an ancestor scope. BUT, USD lets you flip this with
a setting called **binding strength**:

| Setting on the ANCESTOR's binding | Result |
|---|---|
| `"weakerThanDescendants"` (the default) | Child's own binding wins, same as Type A (parent is "weaker than" the child → child wins) |
| `"strongerThanDescendants"` | **Parent's binding wins instead**, even though the child has its own binding authored (parent is "stronger than" the child → parent wins)

**Why this matters**: this is the ONE case where the "who wins" behavior isn't fixed by the
attribute type — it's a dial you can turn yourself, per-binding. Nothing else on this list
works this way; every other type has one fixed rule.

---

## The whole thing in 5 lines

- **Type A**: Child's own number if it has one, otherwise borrow the parent's number. (Primvars, Purpose, drawMode)
- **Type B**: Parent's "off" always wins; child can go off on its own but can't undo an off parent. No numbers involved. (Visibility, Active/Inactive)
- **Type C**: Parent's number and child's number are always mathematically combined — added for translate, multiplied for scale. (Transforms, skeleton joints, point instancer prototypes)
- **Type D**: Child's own number if it has one, otherwise a fixed built-in default — the parent's number is never looked at. (Kind, ordinary attributes, relationships, extent)
- **Type E**: Behaves like Type A by default, but a setting lets you flip it so the parent wins instead. (Material binding strength)

**The single question that tells Type A apart from Type D**: *if the child has nothing set,
does it borrow the parent's value, or does it ignore the parent completely and use a fixed
default instead?* Borrows parent → Type A. Ignores parent → Type D.
