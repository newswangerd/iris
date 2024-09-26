import React, { useState, useRef, useEffect } from "react";
import APIClient from "./api";
import Interpreter from "./components/Interpreter";
import Login from "./components/Login";
import Nav from "./components/Nav";
import ControlPanel from "./components/ControlPanel";
import { ChakraProvider, Box, Spinner, Center, Flex } from "@chakra-ui/react";

const AudioStreamingApp = () => {
  const client = new APIClient();
  const [view, setView] = useState(null);
  const [user, setUser] = useState(null);

  const loginUser = () => {
    client
      .me()
      .then((resp) => {
        setUser((u) => {
          if (!u) {
            setView("interpreter");
          }
          return resp.data;
        });
      })
      .catch((e) => {
        setView("login");
      });
  };

  useEffect(() => {
    const auth_code = new URLSearchParams(window.location.search).get(
      "auth_code",
    );
    if (auth_code) {
      window.history.replaceState({}, document.title, window.location.pathname);
      client.logout().then(() => {
        client.code_login({ auth_code }).then(() => {
          loginUser();
        });
      });
    } else {
      loginUser();
    }

    // return () => null;
  }, [view]);

  return (
    <ChakraProvider>
      <Flex direction={"column"} height={"100svh"}>
        <Box as="header" height="75px" padding={"15px"}>
          <Flex direction={"row"} justifyContent={"space-between"}>
            <Center flex={1} paddingLeft={"15px"}>
              Intelligent Real-time Interpretation System
            </Center>
            <Center>
              <Nav client={client} user={user} setView={(v) => setView(v)} />
            </Center>
          </Flex>
        </Box>
        {renderView(view, client, user, setView)}
      </Flex>
    </ChakraProvider>
  );
};

const renderView = (view, client, user, setView) => {
  switch (view) {
    case "interpreter":
      return <Interpreter client={client} user={user} />;
    case "login":
      return <Login setView={setView} client={client} />;
    case "control_panel":
      return <ControlPanel client={client} />;
    default:
      return (
        <Center>
          <Spinner />
        </Center>
      );
  }
};

export default AudioStreamingApp;
