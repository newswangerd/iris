import React, { useState, useRef, useEffect } from "react";
import { Mic, MicOff, RotateCw } from "lucide-react";
import Message from "./Message";
import { Button, Center, Spinner, Flex, Box } from "@chakra-ui/react";

const Interpreter = ({ client, user }) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef(null);
  const [stream, setStream] = useState(null);
  const ws = useRef(null);
  const wsTranslation = useRef(null);
  const [currentMsg, setCurrentMsg] = useState(null);
  const [sentMsg, setSentMsg] = useState([]);
  const [waitingForMessage, setWaitingForMessage] = useState(false);
  const [hasAudioPerms, setHasAudioPerms] = useState(false);

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
    const translation_ws = new_uri + "/api/ws-translation";

    if (user.role === "admin") {
      console.log("creating translation websocket");
      wsTranslation.current = new WebSocket(translation_ws);
      wsTranslation.current.addEventListener("message", (event) => {
        if (event.data) {
          setSentMsg((oldArray) => [JSON.parse(event.data), ...oldArray]);
        }
      });
    }

    ws.current = new WebSocket(whisper_ws);

    ws.current.addEventListener("message", (event) => {
      setWaitingForMessage(false);
      const data = JSON.parse(event.data);
      if (data.id) {
        setCurrentMsg(data);
      }
    });

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        setHasAudioPerms(true);
        setStream(stream);
      })
      .catch((err) => console.log(err));

    const wsCurrent = ws.current;
    return () => {
      if (wsTranslation.current) {
        wsTranslation.current.close();
      }
      wsCurrent.close();
    };
  }, []);

  const isWebSocketReady = (ws) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return false;
    }
    return true;
  };

  const startRecording = async (e) => {
    if (waitingForMessage) {
      return;
    }
    e.preventDefault();
    e.stopPropagation();

    if (!isWebSocketReady(ws.current)) {
      console.error("WebSocket is not ready");
      return;
    }
    ws.current.send("START");

    const mime = MediaRecorder.isTypeSupported('audio/webm;codecs="opus"')
      ? 'audio/webm;codecs="opus"'
      : "audio/mp4";

    mediaRecorder.current = new MediaRecorder(stream, {
      mimeType: mime,
      audioBitsPerSecond: 16000,
    });
    mediaRecorder.current.start(100);
    mediaRecorder.current.ondataavailable = (event) => {
      if (event.data.size === 0) return;
      if (typeof event.data === "undefined") return;

      ws.current.send(event.data);
    };
    setIsRecording(true);
    setWaitingForMessage(true);
  };

  const stopRecording = (e) => {
    if (mediaRecorder.current) {
      mediaRecorder.current.stop();

      mediaRecorder.current.onstop = () => {
        ws.current.send("STOP");
        setIsRecording(false);
      };
    }
    e.preventDefault();
    e.stopPropagation();
  };

  const acceptMsg = (message) => {
    message.is_accepted = true;
    client.accept_message(message).then(() => {
      setCurrentMsg(null);
      setSentMsg((oldArray) => [message, ...oldArray]);
    });
  };

  const rejectMsg = (message) => {
    message.is_accepted = false;
    client.reject_message(message).then(() => {
      setCurrentMsg(null);
    });
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
            rejectMsg={() => rejectMsg(currentMsg)}
            acceptMsg={() => acceptMsg(currentMsg)}
            message={currentMsg}
            user={user}
          />
        ) : null}
        {sentMsg.map((msg) => (
          <Message user={user} key={msg.id} message={msg} />
        ))}
      </Flex>

      <Box>
        <Center>
          <Button
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            // onMouseLeave={stopRecording}
            onTouchStart={startRecording}
            onTouchEnd={stopRecording}
            onTouchCancel={stopRecording}
            onTouchMove={(e) => e.preventDefault()}
            colorScheme={isRecording || waitingForMessage ? "green" : "red"}
            // isLoading={isRecording || waitingForMessage}
            isDisabled={(waitingForMessage && !isRecording) || !hasAudioPerms}
            size={"lg"}
            height={"75px"}
            width={"100%"}
          >
            {getButtonIcon(
              currentMsg,
              isRecording,
              waitingForMessage,
              hasAudioPerms,
            )}
          </Button>
        </Center>
      </Box>
    </Flex>
  );
};

const getButtonIcon = (
  currentMsg,
  isRecording,
  waitingForMessage,
  hasAudioPerms,
) => {
  if (!hasAudioPerms) {
    return <MicOff size={40} />;
  }
  if (isRecording || waitingForMessage) {
    return <Spinner />;
  }
  if (currentMsg) {
    return <RotateCw size={40} />;
  }
  return <Mic size={40} />;
};

export default Interpreter;
