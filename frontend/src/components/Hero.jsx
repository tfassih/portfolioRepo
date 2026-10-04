import { useEffect, useRef } from "react";
export default function Hero({ name, title }) {
  const root = useRef(null);
  useEffect(() => {
    if (document.documentElement.dataset.intro !== "on") return;
    const timers = [];
    const reduced = matchMedia("(prefers-reduced-motion:reduce)");
    const reset = () => {
      timers.forEach(clearTimeout);
      root.current?.querySelectorAll(".hero-char").forEach((el) => {
        el.textContent = el.textContent.toUpperCase();
        el.style.scale = "1 1";
      });
    };
    root.current.querySelectorAll(".hero-char").forEach((el) => {
      const char = el.textContent;
      const delay = Math.random() * 300;
      [120, 650].forEach((time) =>
        timers.push(
          setTimeout(() => {
            el.textContent =
              Math.random() < 0.5 ? char.toLowerCase() : char.toUpperCase();
            el.style.scale = Math.random() < 0.5 ? "-1 1" : "1 1";
          }, time + delay),
        ),
      );
      timers.push(
        setTimeout(() => {
          el.textContent = char.toUpperCase();
          el.style.scale = "1 1";
        }, 1250 + delay),
      );
    });
    document.addEventListener("motionchange", reset);
    reduced.addEventListener("change", reset);
    return () => {
      timers.forEach(clearTimeout);
      document.removeEventListener("motionchange", reset);
      reduced.removeEventListener("change", reset);
    };
  }, []);
  const characters = (word) =>
    [...word.toUpperCase()].map((char, i) => (
      <span
        className="hero-char"
        aria-hidden="true"
        key={i}
        style={{
          "--delay": `${(i * 71) % 350}ms`,
          "--duration": `${850 + ((i * 83) % 550)}ms`,
        }}
         >
        {char === " " ? "\u00a0" : char}
      </span>
    ));
  return (
    <div ref={root}>
      <h1 className="hero-name" aria-label={name}>
        {name.split(" ").map((word, i) => (
          <span className="name-word" key={i}>
            {characters(word)}
          </span>
        ))}
      </h1>
      <h2 className="hero-title" aria-label={title}>
        {characters(title)}
      </h2>
    </div>
  );
}