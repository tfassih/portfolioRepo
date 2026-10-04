# Portfolio Website as a Portfolio Piece

**Author: Thomas Fassih**

**Public Deployment Date: TBD**

More or less self-explanatory. I had long since outgrown my last portfolio site, which I created around 2019, and decided it's time to put in the legwork to make one that's more than just a glorified gallery for my art.

## What I Wanted vs. What I Had
This time, the site would be written in my languages of choice, not what the deployment platform enforced; if the deployment platform didn't support the language, it was time for a new deployment platform. I have a strong distaste for next.js, and at the time I built the first website it was little more than a static site framework masquerading as full-stack, and it was all that Vercel was compatible with. I chose it because Vercel was free and did what I needed it to at the time. If I'm not doing frontend development, I generally avoid JS in general. I get it, node.js is nifty, but the ecosystem is fragmented beyond belief, and the dependency system is a mess. I'm already completely comfortable with Python, no need to engage in JS exhaustion.  

If this was going to be a worthy portfolio piece, it would need to be a proper full-stack web application. 

**I decided these were my requirements:**
- The site should be fully modular, with only completely new features requiring me to touch the original source code (e.g. adding a section to the art portfolio that allows for in-browser viewing of 3D models).
- The backend would be written in Python, my language of choice for most things.
- The frontend would be written in React, which I've found to be relatively simple and intuitive to implement.
- There would be an admin dashboard for me to view visitor metrics and make any content changes behind-the-scenes.
- Would have a suite of tests integrated into the codebase so if something broke I'd get a notification.
- Would be a unified portfolio showcasing all of my skillsets rather than just my art.
- I would not have to open my wallet at any point to make any of the aforementioned requirements happen.

### Old Site vs New Site Comparison
| Feature | Old Site | New Site |
| ---------------- | ---------------- | ---------------- |
| Backend | None | Python Django |
| Frontend | Next.JS | React via [Astro](https://docs.astro.build/en/concepts/why-astro/) |
| Database | None | PostgreSQL hosted on [Neon Platform](https://neon.tech) |
| Email Subscription | None | [Resend Platform ](https://resend.com/) |
| Deployment Service | [Vercel](https://vercel.com) | [Vercel](https://vercel.com) |
| Static Storage for Media | [GitHub Repo](https://github.com) and [YouTube](https://youtube.com) | [Google Drive](drive.google.com) |
| Gross/Net Cost | $0/$0 | $0/$0 |
| Modular | No | Yes |

It took an evening to get it coded and wired together, running locally and sniff tested. Not bad. I'll have an AI put together a guide for how I went about it and publish it to the new site at some point. Until then, this is it.






