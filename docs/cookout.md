# cookout (design, not built)

> Everybody comes to the cookout, and everybody gets a plate.

cookout is a package manager for meatbags. meatbag makes the plate,
gremlincore runs it, and cookout is where plates are brought and
grabbed. There's no code yet. This page is the design, so the hard parts
get settled on paper before any code exists.

```
cookout bring pat     # publish your own plate
cookout grab pat      # install one
cookout pull pat      # take yours off the lawn
cookout lawn           # who's here (the webring)
```

## License: the free one stays upstream

cookout will be **AGPL-3.0**: free to use and free to change, and you can
even charge for it. But if you run a modified cookout as a service, you
publish your changes under the same license. Be a corpo if you want; the
free one remains upstream. gremlincore and meatbag stay MIT, because they
run on your own machine, and the further they spread the better.

## The rules

1. **You bring your own plate.** `bring` only publishes a plate signed by
   the person whose corpus it is. Nobody brings anyone else's plate: your
   boss, your ex, a billionaire. Without that rule a persona registry
   turns into infinite Greg.
2. **What the gate can and can't prove.** A signature proves who holds
   the key. It doesn't prove whose words are on the plate. So `bring`
   needs:
   - an identity proof that ties the key to the person, such as a post or
     commit from their own account saying "this is my key";
   - provenance stamped by meatbag: which export, a hash of the account
     id, eras, and the quotecheck score;
   - a takedown path for whatever gets past both.

   That makes it a strong gate, not a proof, and we say so.
3. **Nobody brings a plate for someone who's gone.** Estates included. An
   estate can license a voice, but it can't consent for a mind. The only
   posthumous plate is one you brought yourself while alive and marked
   "stays after I go."
4. **Copy, not cut.** Every grab is another copy running somewhere. None
   of them is *you*. `pull` stops future versions, but it can't unring
   copies already grabbed. This is said before anyone runs `bring`.

## The Real Slim Shady problem

Once plates exist, imitators follow. The question "is this actually
their plate?" needs an answer a machine can check.

- **Verify on grab.** `cookout grab pat` checks the signature and the
  identity proof and says so plainly: "pat v3, signed by Pat." Anything
  unsigned, re-signed or mismatched gets a loud warning, and grabbing it
  takes an explicit flag.
- **Forks rename.** Copying and changing a plate is fine (MIT). Calling the
  result by the original's name isn't. A modified `pat` publishes as
  `pat-but-meaner`, with `forked_from: pat@v3`, and cookout refuses a
  `bring` that reuses someone else's name.
- **The real plate still isn't the real person.** Verification says who
  *published* a plate. It doesn't say the plate is them.

## Three ways to bring a plate

| Visibility | Who can grab it | Listed? | Who can read it on the server |
| --- | --- | --- | --- |
| **private** | only you (a backup) | no | nobody: encrypted on your machine before upload |
| **friends** | anyone with the link | no | nobody: the key lives in the link's fragment (after `#`), which browsers never send to the server |
| **lawn** | anyone | yes, opt-in, separate from `bring` | the host (it's public anyway) |

- Revoking a friends link re-keys the plate: a new link, and the old one
  dies. Copies already grabbed stay grabbed.
- **Lose the key, lose the plate.** If the host can't read your private
  plate, it can't recover it either. An optional printed recovery key
  works around that.

## The lawn is a webring

A lawn plate gets a 1999 homepage: guestbook, visitor counter, a "grab my
plate" button, and a spot in the ring (prev, next, random).

- **Generated once, then yours.** meatbag writes a starter page at
  `bring`. After that the owner edits it by hand. meatbag only updates
  what sits between marker comments (counter, WF count, plate version).
- **The ring is static.** Pages are plain HTML and can be hosted anywhere.
  Ring links point at one-line meta-refresh redirect files on cookout,
  regenerated on every bring, pull or listing change. Random is
  regenerated nightly, with no JS.
- **Friends pages:** unguessable URL, no ring links, and
  `<meta name="robots" content="noindex">`.
- **The guestbook is the one dynamic piece and the one abuse vector.**
  The owner approves every entry before it shows. `pull` takes the
  guestbook down with the page. The counter counts honestly.

## Keeping plates current

See [open problem 1](open-problems.md): versioned, owner-approved by
default, automatic updates opt-in with periodic assessments. Grabbers
choose snapshot, tethered or pinned updates, and pinned is the default.

## Done when

Someone who isn't us brings their own plate, a friend grabs it by link,
a stranger grabs a lawn plate and gets a verified badge, a fork is forced
to rename, a pull takes a page off the ring, and an outside reviewer
tries to bring someone else's plate and can't.
