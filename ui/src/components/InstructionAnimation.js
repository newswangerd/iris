import React, { useState, useEffect, useContext } from "react";
import { TranslationsContext } from "../context.js";

import { Speech } from "lucide-react";

const ButtonAnimation = () => {
  const [animate, setAnimate] = useState(true);

  const t = useContext(TranslationsContext);

  useEffect(() => {
    setAnimate(true);
  }, []);

  const handleClick = () => {
    setAnimate(false);
    setTimeout(() => setAnimate(true), 10);
  };

  return (
    <div className="container">
      <div className="animation-wrapper">
        <div className={`speaker-icon ${animate ? "animate" : ""}`}>
          <Speech size={48} />
        </div>
        <div className={`text ${animate ? "animate" : ""}`}>
          {t("Your translated message.")}
        </div>

        <div className="button-wrapper">
          <button
            className={`button ${animate ? "animate" : ""}`}
            onClick={handleClick}
          />
          <div className={`finger ${animate ? "animate" : ""}`} />
        </div>
      </div>
      <style jsx>{`
        .container {
          display: flex;
          justify-content: center;
          align-items: center;
          font-family: Arial, sans-serif;
        }
        .animation-wrapper {
          display: flex;
          flex-direction: column;
          align-items: center;
          width: 400px;
        }
        .speaker-icon {
          opacity: 0;
          margin-top: 20px;
        }
        .button-wrapper {
          position: relative;
          width: 300px;
          height: 60px;
          margin: 20px 0;
        }
        .finger {
          position: absolute;
          width: 40px;
          height: 60px;
          background-color: #f9d9c0;
          border-radius: 20px 20px 10px 10px;
          top: -30px;
          left: 50%;
          transform: translateX(-50%) rotate(315deg);
          opacity: 0;
          z-index: 2;
        }
        .button {
          position: absolute;
          width: 100%;
          height: 100%;
          border: none;
          border-radius: 10px;
          background-color: red;
          cursor: pointer;
          z-index: 1;
        }
        .text {
          font-size: 18px;
          opacity: 0;
          margin-top: 10px;
        }
        @keyframes buttonAnimation {
          0%,
          20%,
          80%,
          100% {
            background-color: red;
          }
          25%,
          75% {
            background-color: green;
          }
        }
        @keyframes fingerAnimation {
          0%,
          100% {
            opacity: 0;
            top: -30px;
          }
          5% {
            opacity: 1;
            top: -30px;
          }
          10%,
          70% {
            opacity: 1;
            top: -10px;
          }
          75% {
            opacity: 0;
            top: -30px;
          }
        }
        @keyframes speakerAnimation {
          0%,
          30%,
          75%,
          100% {
            opacity: 0;
          }
          35%,
          70% {
            opacity: 1;
          }
        }
        @keyframes textAnimation {
          0%,
          75% {
            opacity: 0;
          }
          80%,
          100% {
            opacity: 1;
          }
        }
        .button.animate {
          animation: buttonAnimation 6s infinite;
        }
        .finger.animate {
          animation: fingerAnimation 6s infinite;
        }
        .speaker-icon.animate {
          animation: speakerAnimation 6s infinite;
        }
        .text.animate {
          animation: textAnimation 6s infinite;
        }
      `}</style>
    </div>
  );
};

export default ButtonAnimation;
