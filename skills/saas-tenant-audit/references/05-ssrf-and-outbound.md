# 05 — Server-side request forgery and other outbound requests

Contents: find the sinks · design of a single guarded fetcher · test list · verification
without the target's HTTP extension

## 1. Find every sink, not only the named one (FL-15)

An audit finding usually names one function ("fetches a user URL"). Grep for **all**
outbound call sites:

- HTTP client facades/libraries, raw `curl`, `file_get_contents`/`fopen` on URLs, image
  libraries that accept URLs, PDF/HTML renderers, webhook senders, RSS/OG/link-preview
  fetchers, "import from URL" features, third-party "reader"/"screenshot" services that
  you forward the user URL to.
- **Second-order fetches**: URLs the server extracts from a page it just fetched
  (stylesheets, images, redirects, `<link>`, sitemap entries). The first hop was
  validated; the second was not.
- Stored URLs used later by jobs (avatar URL, webhook URL, callback URL).
- What you *send* to third parties: forwarding a user-supplied URL to an external reader
  is a data-disclosure and trust decision, not just an SSRF one.
- **Headless-browser, PDF and screenshot renderers** that load user-controlled URLs or HTML: IP pinning inside your own code does not cover what the browser fetches. Restrict egress at the network layer or through a filtering proxy, and disable `file://` access and, where possible, JavaScript. For **blind** SSRF (the response is never shown), use an out-of-band listener that *you* own — never a third party's.

## 2. Guard design (put it in ONE component and route every sink through it)

1. **Scheme** allow-list: `http`/`https` only. Reject userinfo (`user:pass@`), whitespace,
   backslashes, control characters, and names without a dot (`localhost`, single-label
   hosts).
2. **Port** allow-list (e.g. 80/443). This alone neutralises many internal services,
   including internal app ports that happen to be reachable.
3. **Resolve, then judge the IP**, not the string. Normalise numeric forms
   (`2130706433`, `0x7f.1`, `0177.0.0.1`, `127.1`). Reject if *any* resolved address is
   non-public: loopback, RFC1918, link-local (cloud metadata), CGNAT `100.64/10`, `0/8`,
   multicast/reserved; for IPv6 allow only global unicast and reject `::1`, link-local,
   unique-local, IPv4-mapped, 6to4, NAT64 forms.
4. **Rebuild the URL from validated parts.** Never hand the original string to the client
   (parser differentials: `http://a\@127.0.0.1`, `http://127.0.0.1#@example.com`).
5. **Pin the validated IP** for the connection (e.g. curl resolve override) so a second
   DNS answer cannot rebind to an internal address.
6. **Redirects**: do not auto-follow. Follow manually with a hop limit and re-run the whole
   guard on every hop.
7. **TLS verification on**; no environment-proxy usage that bypasses the guard.
8. **Content-Type allow-list** per use (HTML, CSS, plain text) and a **decoded-size**
   limit enforced by a sink that aborts the transfer (defends against compression bombs;
   a `Content-Length` check alone is not enough).
9. **Timeouts** for connect and total.
10. **User-facing message is generic** ("this URL cannot be analysed"); the reason and the
    user id go to the log, **not the URL**.

## 3. Tests to run (all against your own scratch tenant)

- Private and special addresses in every notation listed above; IPv6 variants.
- A hostname you control that resolves to a private address (DNS rebinding, and
  "one public + one private" A records).
- Redirect to a private address, redirect chains beyond the hop limit.
- Redirect that changes scheme/port.
- Non-HTML content served for an HTML feature; a compressed response that expands beyond
  the limit; a very slow response.
- Second-order: a page whose stylesheet/image URL points at a private address.
- Confirm the **positive control**: a normal public URL still works.
- Confirm the block is logged with reason and no URL.

## 4. When the local environment cannot exercise the real client (FL-31)

If the local runtime lacks the HTTP extension that production uses, test the pin/abort
behaviour on the real host with a **scratch harness**: a loopback test server plus a guard
subclass that relaxes only the loopback rule. Check: pin works even when the hostname is
not resolvable, an oversized compressed body aborts early with bounded memory, a
self-signed certificate is rejected, redirects to private ranges are blocked. Afterwards
confirm the test server's port is closed (built-in servers may fork workers that survive a
kill of the parent) and delete the harness. (FL-34)

## 5. Residual risk to state

- Guarded fetch does not stop the *content* being hostile (parse safely, sanitise output).
- Forwarding URLs to third-party readers still discloses them.
- Internal services reachable on allowed ports (80/443) remain in scope; segment the
  network as well.
