import React, { useState, useRef, useEffect, useContext } from "react";
import { Mic, MicOff } from "lucide-react";
import Message from "./Message";
import { Button, Center, Spinner, Flex, Box, Divider } from "@chakra-ui/react";
import { UserContext } from "../context.js";
import InstructionModal from "./InstructionModal";

import Recoder from "opus-recorder";

const Interpreter = ({ client, showInstructions }) => {
  const [isRecording, setIsRecording] = useState(false);
  const ws = useRef(null);
  const [sentMsg, setSentMsg] = useState([]);
  const synth = window.speechSynthesis;
  // const [isConversationMode, setIsConversationMode] = useState(
  //   localStorage.getItem("isConversationMode") === "true" ? true : false,
  // );
  const [isConversationMode, setIsConversationMode] = useState(true);

  const [oggRecorder, setOggRecorder] = useState(null);
  const [isVisible, setIsVisible] = useState(true);

  const micStreams = useRef([]);

  const user = useContext(UserContext);

  useEffect(() => {
    if (!isVisible) return;

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        // This is a stupid solution to get around react's stupid strict mode.
        // I can't figure out how to cancel this promise in the clenup function
        // so we're going to get around this by just saving all the streams that
        // get created and clean them all up.
        micStreams.current.push(stream);
        console.log("creating stream");
        const context = new AudioContext();
        const sourceNode = context.createMediaStreamSource(stream);
        setOggRecorder(
          new Recoder({
            sourceNode: sourceNode,
            streamPages: true,
            encoderSampleRate: 16000,
            numberOfChannels: 1,
            encoderFrameSize: 20,
            maxFramesPerPage: 10,
          }),
        );
      })
      .catch((err) => console.log(err));
    return () => {
      micStreams.current.forEach((stream) =>
        stream.getTracks().forEach((track) => track.stop()),
      );
      micStreams.current = [];
      setOggRecorder(null);
    };
  }, [isVisible]);

  useEffect(() => {
    const callback = (event) => {
      setIsVisible(!document.hidden);
    };
    document.addEventListener("visibilitychange", callback);
    return () => document.removeEventListener("visibilitychange", callback);
  }, []);

  useEffect(() => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) return;
    if (!oggRecorder) return;

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

    oggRecorder.ondataavailable = (data) => {
      ws.current.send(data);
    };

    client.get_recent_messages().then((resp) => {
      setSentMsg(resp.data);
    });

    const wsCurrent = ws.current;

    return () => {
      wsCurrent.close();
    };
  }, [oggRecorder]);

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

    if (ws.current && ws.current.readyState !== WebSocket.OPEN) {
      window.location.reload();
      return;
    }

    oggRecorder.onstart = () => {
      setIsRecording(true);

      const start_msg = "START:";

      const stream_meta = {};

      if (isConversationMode) {
        stream_meta.mode = "conversation";
      } else {
        stream_meta.mode = "normal";
      }

      ws.current.send(start_msg + JSON.stringify(stream_meta));
    };

    oggRecorder.start();
  };

  const stopRecording = (e, cancel = false) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    if (!isRecording) return;

    oggRecorder.onstop = () => {
      setIsRecording(false);

      if (cancel) {
        ws.current.send("CANCEL:{}");
      } else {
        ws.current.send("STOP:{}");
      }
    };

    oggRecorder.stop();
  };

  const acceptMsg = (message, modifiedText) => {
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
            isDisabled={!oggRecorder}
            size={"lg"}
            height={"125px"}
            width={"100%"}
          >
            {getButtonIcon(isRecording, oggRecorder)}
          </Button>
        </Center>
      </Box>
    </Flex>
  );
};

const getButtonIcon = (isRecording, oggRecorder) => {
  if (!oggRecorder) {
    // return <Fingerprint size={40} />;
    return <MicOff size={40} />;
  }
  if (isRecording) {
    return <Spinner style={{ pointerEvents: "none" }} />;
  }

  // "pointerEvents: none" prevents the button from getting stuck
  return (
    <>
      <Mic size={40} style={{ pointerEvents: "none" }} />
    </>
  );
};

export default Interpreter;
