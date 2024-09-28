import React, { useState, useRef, useEffect, useContext } from "react";
import { Mic, MicOff, RotateCw } from "lucide-react";
import Message from "./Message";
import { Button, Center, Spinner, Flex, Box, Divider } from "@chakra-ui/react";
import { UserContext } from "../context.js";
import InstructionModal from "./InstructionModal";

import Recoder from "opus-recorder";

const Interpreter = ({ client, showInstructions }) => {
  const [isRecording, setIsRecording] = useState(false);
  const ws = useRef(null);
  const [sentMsg, setSentMsg] = useState([]);
  const [hasAudioPerms, setHasAudioPerms] = useState(false);
  const synth = window.speechSynthesis;
  // const [isConversationMode, setIsConversationMode] = useState(
  //   localStorage.getItem("isConversationMode") === "true" ? true : false,
  // );
  const [isConversationMode, setIsConversationMode] = useState(true);

  const oggRecorder = useRef(null);

  const user = useContext(UserContext);

  const wsEvent = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id) {
      if (
        msg.is_accepted &&
        (msg.user === user.name || msg.language !== user.language)
      ) {
        setSentMsg((oldArray) => [JSON.parse(event.data), ...oldArray]);
        if (msg.user !== user.name) {
          // if (msg.translated_text[user.language] && isConversationMode) {
          //   sayTTS(msg, user.language);
          // }
        }
      }
    }
  };

  const connectWS = () => {
    if (!ws.current || ws.current.readyState === WebSocket.CLOSED) {
      // Initialize WebSocket connection
      var loc = window.location,
        new_uri;
      if (loc.protocol === "https:") {
        new_uri = "wss:";
      } else {
        new_uri = "ws:";
      }
      new_uri += "//" + loc.host;

      const whisper_ws = new_uri + "/api/ws-whisper";

      ws.current = new WebSocket(whisper_ws);
      ws.current.addEventListener("message", wsEvent);
    }
  };

  useEffect(() => {
    connectWS();

    if (
      (oggRecorder.current &&
        oggRecorder.current.audioContext.state !== "running") ||
      !oggRecorder.current
    ) {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          const context = new AudioContext();
          const sourceNode = context.createMediaStreamSource(stream);
          oggRecorder.current = new Recoder({
            sourceNode: sourceNode,
            streamPages: true,
            encoderSampleRate: 16000,
            numberOfChannels: 1,
            encoderFrameSize: 20,
            maxFramesPerPage: 10,
          });

          oggRecorder.current.on_start = () => {};

          oggRecorder.current.ondataavailable = (data) => {
            ws.current.send(data);
          };

          setHasAudioPerms(true);
        })
        .catch((err) => console.log(err));
    }

    client.get_recent_messages().then((resp) => {
      setSentMsg(resp.data);
    });

    return () => {
      if (ws.current.readyState === WebSocket.OPEN) ws.current.close();
    };
  }, []);

  useEffect(() => {
    ws.current.addEventListener("message", wsEvent);
    return () => ws.current.removeEventListener("message", wsEvent);
  }, [isConversationMode, user]);

  // useEffect(() => {
  //   localStorage.setItem("isConversationMode", String(isConversationMode));
  // }, [isConversationMode]);

  const sayTTS = (message, lang) => {
    const utterance = new SpeechSynthesisUtterance(
      message.translated_text[lang],
    );
    utterance.lang = lang;
    synth.speak(utterance);
  };

  const startRecording = async (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    if (isRecording) return;
    if (oggRecorder.current.state === "loading") return;

    if (ws.current.readyState !== WebSocket.OPEN) {
      window.location.reload();
      return;
    }

    oggRecorder.current.onstart = () => {
      const start_msg = "START:";

      const stream_meta = {};

      if (isConversationMode) {
        stream_meta.mode = "conversation";
      } else {
        stream_meta.mode = "normal";
      }

      ws.current.send(start_msg + JSON.stringify(stream_meta));
    };

    oggRecorder.current.start();

    setIsRecording(true);
  };

  const stopRecording = (e, cancel = false) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    if (!isRecording) return;

    oggRecorder.current.onstop = () => {
      setIsRecording(false);

      if (cancel) {
        ws.current.send("CANCEL:{}");
      } else {
        ws.current.send("STOP:{}");
      }
    };

    oggRecorder.current.stop();
  };

  const acceptMsg = (message, modifiedText) => {
    console.log(message);
    console.log(modifiedText);
    client.accept_message(message, modifiedText).then(() => {});
  };

  return (
    <Flex direction={"column"} flex={1}>
      <InstructionModal showOnLoad={showInstructions} />
      <Flex
        flex={"1 1 0"}
        style={{ overflow: "auto" }}
        flexDirection={"column-reverse"}
      >
        {sentMsg.map((msg, k) => (
          <Message
            acceptMsg={acceptMsg}
            sayTTS={sayTTS}
            user={user}
            key={k}
            message={msg}
          />
        ))}
      </Flex>

      <Box paddingTop={"20px"}>
        <Divider />
        <Center>
          <Button
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            // onMouseLeave={stopRecording}
            onTouchStart={startRecording}
            onTouchEnd={stopRecording}
            onTouchCancel={stopRecording}
            onTouchMove={(e) => e.preventDefault()}
            colorScheme={isRecording ? "green" : "red"}
            isDisabled={!hasAudioPerms}
            size={"lg"}
            height={"125px"}
            width={"100%"}
          >
            {getButtonIcon(isRecording, hasAudioPerms)}
          </Button>
        </Center>
      </Box>
    </Flex>
  );
};

const getButtonIcon = (isRecording, hasAudioPerms) => {
  if (!hasAudioPerms) {
    // return <Fingerprint size={40} />;
    return <MicOff size={40} />;
  }
  if (isRecording) {
    return <Spinner />;
  }

  return (
    <>
      <Mic size={40} />
    </>
  );
};

export default Interpreter;
