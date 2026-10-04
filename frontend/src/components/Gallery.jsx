import { useEffect, useRef, useState } from "react";
function preload(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const timer = setTimeout(() => reject(new Error("Timeout")), 20000);
    image.onload = async () => {
      try {
        await image.decode();
        clearTimeout(timer);
        resolve();
      } catch (e) {
        clearTimeout(timer);
        reject(e);
      }
    };
    image.onerror = () => {
      clearTimeout(timer);
      reject(new Error("Image unavailable"));
    };
    image.src = src;
  });
}
export default function Gallery({ items, kind }) {
  const [index, setIndex] = useState(0);
  const [state, setState] = useState("loading");
  const [attempt, setAttempt] = useState(0);
  const [buffering, setBuffering] = useState(true);
  const [videoError, setVideoError] = useState(false);
  const [described, setDescribed] = useState(false);
  const dialog = useRef(null);
  const opener = useRef(null);
  const video = useRef(null);
  useEffect(() => {
    let cancelled = false;
    let fadeTimer;
    setState("loading");
    const urls = items.map((item) =>
      kind === "images" ? item.asset.src : item.poster.src,
    );
    Promise.all([...new Set(urls)].map(preload))
      .then(() => {
        if (!cancelled) {
          setState("fading");
          fadeTimer = setTimeout(() => setState("ready"), 220);
        }
      })
      .catch(() => {
        if (!cancelled) setState("error");
      });
    return () => {
      cancelled = true;
      clearTimeout(fadeTimer);
    };
  }, [items, kind, attempt]);
  if (!items.length) return <p className="empty">COMING SOON</p>;
  const item = items[index];
  const change = (delta) => {
    video.current?.pause();
    setIndex((index + delta + items.length) % items.length);
    setBuffering(true);
    setVideoError(false);
    setDescribed(false);
  };
  const close = () => {
    dialog.current.close();
    opener.current?.focus();
  };
  return (
    <section
      className="gallery"
      aria-label={kind === "images" ? "Image gallery" : "Video gallery"}
    >
      {["loading", "fading"].includes(state) && (
        <div
          className={`gallery-cover ${state === "fading" ? "fading" : ""}`}
          role="status"
        >
          <span className="spinner" aria-hidden="true" />
          Loading {kind === "images" ? "images" : "posters"}…
        </div>
      )}
      {state === "error" && (
        <div role="alert">
          <p>
            The gallery could not finish loading. Check your connection and try again.
          </p>
          <button onClick={() => setAttempt(attempt + 1)}>Retry gallery</button>
        </div>
      )}
      {state === "ready" && (
        <div className="gallery-ready">
          <div className="gallery-stage">
            {kind === "images" ? (
              <button
                ref={opener}
                onClick={() => dialog.current.showModal()}
                aria-label={`Open ${item.title} fullscreen`}
              >
                <img src={item.asset.src} alt={item.asset.alt} />
              </button>
            ) : (
              <video
                key={`${item.id}-${described}`}
                ref={video}
                src={
                  described && item.described_video
                    ? item.described_video.src
                    : item.asset.src
                }
                poster={item.poster.src}
                controls
                playsInline
                preload="auto"
                crossOrigin="anonymous"
                aria-label={item.title}
                onCanPlay={() => setBuffering(false)}
                onWaiting={() => setBuffering(true)}
                onPlaying={() => setBuffering(false)}
                onError={() => {
                  setVideoError(true);
                  setBuffering(false);
                }}
                >
                {item.captions && (
                  <track
                    kind="captions"
                    src={item.captions.src}
                    srcLang="en"
                    label="English"
                    default
                  />
                )}
                Your browser cannot play this video.
              </video>
            )}
          </div>
          {kind === "videos" && (
            <div>
              <p role="status">
                {videoError
                  ? "Video could not load."
                  : buffering
                    ? "Buffering selected video…"
                    : ""}
              </p>
              {videoError && (
                <button
                  onClick={() => {
                    setVideoError(false);
                    setBuffering(true);
                    video.current.load();
                  }}
                >
                  Retry video
                </button>
              )}
              {item.described_video && (
                <button
                  onClick={() => {
                    setDescribed(!described);
                    setBuffering(true);
                  }}
                  aria-pressed={described}
                >
                  Audio-described version {described ? "on" : "off"}
                </button>
              )}
            </div>
          )}
          <div className="gallery-caption">
            <div key={item.id} className="gallery-ready">
              <h2>{item.title}</h2>
              <div
                className="prose"
                dangerouslySetInnerHTML={{ __html: item.description_html }}
              />
            </div>
            <div className="gallery-toolbar">
              <button onClick={() => change(-1)} aria-label="Previous item">
                ←
              </button>
              <span aria-live="polite" aria-atomic="true">
                {index + 1} / {items.length}: {item.title}
              </span>
              <button onClick={() => change(1)} aria-label="Next item">
                →
              </button>
            </div>
          </div>
          {item.transcript_html && (
            <details>
              <summary>Read transcript / visual description</summary>
              <div
                className="prose"
                dangerouslySetInnerHTML={{ __html: item.transcript_html }}
              />
            </details>
          )}
          {kind === "images" && (
            <dialog
              className="lightbox"
              ref={dialog}
              aria-label={item.title}
              onCancel={() => opener.current?.focus()}
            >
              <button
                className="close"
                onClick={close}
                aria-label="Close fullscreen image"
              >
                × Close
              </button>
              <img src={item.asset.src} alt={item.asset.alt} />
            </dialog>
          )}
        </div>
      )}
    </section>
  );
}