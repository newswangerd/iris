import React, { useState, useRef, useEffect } from "react";
import { Mic, MicOff, Fingerprint, RotateCw } from "lucide-react";
import Message from "./Message";
import { Button, Center, Spinner, Flex, Box, Divider } from "@chakra-ui/react";

function waitForSocketConnection(socket, callback) {
  setTimeout(function () {
    if (socket.readyState === 1) {
      console.log("Connection is made");
      if (callback != null) {
        callback();
      }
    } else {
      console.log("wait for connection...");
      waitForSocketConnection(socket, callback);
    }
  }, 5); // wait 5 milisecond for the connection...
}

const Interpreter = ({ client, user }) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef(null);
  const [stream, setStream] = useState(null);
  const ws = useRef(null);
  const [currentMsg, setCurrentMsg] = useState(null);
  const [sentMsg, setSentMsg] = useState([]);
  const [waitingForMessage, setWaitingForMessage] = useState(false);
  const [hasAudioPerms, setHasAudioPerms] = useState(false);
  const synth = window.speechSynthesis;

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

    ws.current.addEventListener("message", (event) => {
      setWaitingForMessage(false);
      const msg = JSON.parse(event.data);
      console.log(msg);
      if (msg.id) {
        if (msg.user === user.name && msg.is_accepted === null) {
          setCurrentMsg(msg);
        } else if (msg.user === user.name || msg.language !== user.language) {
          setSentMsg((oldArray) => [JSON.parse(event.data), ...oldArray]);
        }
      }
    });

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        setHasAudioPerms(true);
        setStream(stream);
      })
      .catch((err) => console.log(err));

    return () => {
      ws.current.close();
    };
  }, []);

  useEffect(() => {
    client.get_recent_messages().then((resp) => {
      console.log(resp.data);
      setSentMsg(resp.data);
    });
  }, []);

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
    if (waitingForMessage) {
      return;
    }
    e.preventDefault();
    e.stopPropagation();

    if (!isWebSocketReady(ws.current)) {
      console.error("WebSocket is not ready");
      return;
    }
    const start_msg = "START:";

    if (currentMsg) {
      ws.current.send(start_msg + currentMsg.id);
    } else {
      ws.current.send(start_msg);
    }

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
            colorScheme={isRecording || waitingForMessage ? "green" : "red"}
            // isLoading={isRecording || waitingForMessage}
            isDisabled={(waitingForMessage && !isRecording) || !hasAudioPerms}
            size={"lg"}
            height={"125px"}
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
    // return <Fingerprint size={40} />;
    return <MicOff size={40} />;
  }
  if (isRecording || waitingForMessage) {
    return <Spinner />;
  }
  if (currentMsg) {
    return <RotateCw size={40} />;
  }
  return (
    <>
      <Mic size={40} />
      <Fingerprint size={40} />
    </>
  );

  // return <Mic size={40} />;
};

export default Interpreter;
