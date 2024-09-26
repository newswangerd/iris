import React, { useState, useRef, useEffect } from "react";
import { Mic, MicOff, Fingerprint, RotateCw } from "lucide-react";
import Message from "./Message";
import {
  Button,
  Center,
  Spinner,
  Flex,
  Box,
  Divider,
  FormControl,
  FormLabel,
  Switch,
} from "@chakra-ui/react";

import Recoder from "opus-recorder";

const Interpreter = ({ client, user }) => {
  const [isRecording, setIsRecording] = useState(false);
  const ws = useRef(null);
  const [currentMsg, setCurrentMsg] = useState(null);
  const [sentMsg, setSentMsg] = useState([]);
  const [hasAudioPerms, setHasAudioPerms] = useState(false);
  const synth = window.speechSynthesis;
  const [isConversationMode, setIsConversationMode] = useState(
    localStorage.getItem("isConversationMode") === "true" ? true : false,
  );
  const oggRecorder = useRef(null);

  useEffect(() => {
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

    return () => {
      ws.current.close();
    };
  }, []);

  useEffect(() => {
    const wsEvent = (event) => {
      console.log(isConversationMode);

      const msg = JSON.parse(event.data);
      if (msg.id) {
        console.log(msg.text);
        if (msg.user === user.name && msg.is_accepted === null) {
          setCurrentMsg(msg);
        } else if (
          msg.is_accepted &&
          (msg.user === user.name || msg.language !== user.language)
        ) {
          setSentMsg((oldArray) => [JSON.parse(event.data), ...oldArray]);
          if (msg.user !== user.name) {
            console.log(msg.translated_text[user.language]);
            console.log(isConversationMode);
            if (msg.translated_text[user.language] && isConversationMode) {
              sayTTS(msg, user.language);
            }
          }
        }
      }
    };
    ws.current.addEventListener("message", wsEvent);
    return () => ws.current.removeEventListener("message", wsEvent);
  }, [isConversationMode, user]);

  useEffect(() => {
    client.get_recent_messages().then((resp) => {
      console.log(resp.data);
      setSentMsg(resp.data);
    });
  }, []);

  useEffect(() => {
    localStorage.setItem("isConversationMode", String(isConversationMode));
  }, [isConversationMode]);

  const sayTTS = (message, lang) => {
    const utterance = new SpeechSynthesisUtterance(
      message.translated_text[lang],
    );
    utterance.lang = lang;
    synth.speak(utterance);
  };

  const isWebSocketReady = (ws) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return false;
    }
    return true;
  };

  const startRecording = async (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    if (!isWebSocketReady(ws.current)) {
      console.error("WebSocket is not ready");
      return;
    }

    oggRecorder.current.onstart = () => {
      const start_msg = "START:";

      const stream_meta = {};

      if (currentMsg) {
        stream_meta.re_recording = currentMsg.id;
      }

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

  const acceptMsg = (message) => {
    message.is_accepted = true;
    setCurrentMsg(null);
    // setSentMsg((oldArray) => [message, ...oldArray]);
    client.accept_message(message).then(() => {});
  };

  const rejectMsg = (message) => {
    message.is_accepted = false;
    setCurrentMsg(null);
    client.reject_message(message).then(() => {});
  };

  return (
    <Flex direction={"column"} flex={1}>
      <Flex
        flex={"1 1 0"}
        style={{ overflow: "auto" }}
        flexDirection={"column-reverse"}
      >
        {currentMsg ? (
          <Message
            key={-1}
            rejectMsg={() => rejectMsg(currentMsg)}
            acceptMsg={() => acceptMsg(currentMsg)}
            message={currentMsg}
            user={user}
            sayTTS={sayTTS}
          />
        ) : null}
        {sentMsg.map((msg, k) => (
          <Message sayTTS={sayTTS} user={user} key={k} message={msg} />
        ))}
        <Box key={-2} padding={"20px"}>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb="0">Enable conversation mode?</FormLabel>
            <Switch
              onChange={(e) => {
                setIsConversationMode(!isConversationMode);
              }}
              isChecked={isConversationMode}
            />
          </FormControl>
        </Box>
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
            {getButtonIcon(currentMsg, isRecording, hasAudioPerms)}
          </Button>
        </Center>
      </Box>
    </Flex>
  );
};

const getButtonIcon = (currentMsg, isRecording, hasAudioPerms) => {
  if (!hasAudioPerms) {
    // return <Fingerprint size={40} />;
    return <MicOff size={40} />;
  }
  if (isRecording) {
    return <Spinner />;
  }
  if (currentMsg) {
    return <RotateCw size={40} />;
  }
  return (
    <>
      <Mic size={40} />
    </>
  );

  // return <Mic size={40} />;
};

export default Interpreter;
