import React, { useState, useEffect } from "react";
import APIClient from "./api";
import Interpreter from "./components/Interpreter";
import Login from "./components/Login";
import Nav from "./components/Nav";
import ControlPanel from "./components/ControlPanel";
import { ChakraProvider, Box, Spinner, Center, Flex } from "@chakra-ui/react";

import { UserContext, TranslationsContext } from "./context.js";

const AudioStreamingApp = () => {
  const client = new APIClient();
  const [view, setView] = useState(null);
  const [user, setUser] = useState(null);
  const [translations, setTranslations] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);
  const [userAuthed, setUserAuthed] = useState(false);

  const loginUser = () => {
    client
      .me()
      .then((resp) => {
        setUser((u) => {
          setUserAuthed(true);
          setView("interpreter");
          return resp.data;
        });
      })
      .catch((e) => {
        setView("login");
        setUserAuthed(true);
      });
  };

  useEffect(() => {
    if (userAuthed) {
      let lang;
      if (!user) {
        lang = "en";
      } else {
        lang = user.language;
      }
      client.get_translations(lang).then((resp) => {
        setTranslations(resp.data);
      });
    }
  }, [user, userAuthed]);

  useEffect(() => {
    const auth_code = new URLSearchParams(window.location.search).get(
      "auth_code",
    );
    if (auth_code) {
      window.history.replaceState({}, document.title, window.location.pathname);
      client.logout().then(() => {
        client.code_login({ auth_code }).then(() => {
          setShowInstructions(true);

          loginUser();
        });
      });
    } else {
      loginUser();
    }

    // return () => null;
  }, []);

  const getTranslation = (msg) => {
    if (!translations) {
      return "";
    }
    if (translations["messages"][msg] === undefined) {
      return "MISSING TRANSLATION: " + msg;
    }
    return translations["messages"][msg];
  };

  return (
    <UserContext.Provider value={user}>
      <TranslationsContext.Provider value={getTranslation}>
        <ChakraProvider>
          <Flex direction={"column"} height={"100svh"}>
            <Box as="header" height="75px" padding={"15px"}>
              <Flex direction={"row"} justifyContent={"space-between"}>
                <Center flex={1} paddingLeft={"15px"}>
                  Intelligent Real-time Interpretation System
                </Center>
                <Center>
                  <Nav
                    client={client}
                    user={user}
                    setView={(v) => setView(v)}
                  />
                </Center>
              </Flex>
            </Box>
            {translations ? (
              renderView(view, client, setView, showInstructions)
            ) : (
              <Center>
                <Spinner />
              </Center>
            )}
          </Flex>
        </ChakraProvider>
      </TranslationsContext.Provider>
    </UserContext.Provider>
  );
};

const renderView = (view, client, setView, showInstructions) => {
  switch (view) {
    case "interpreter":
      return (
        <Interpreter showInstructions={showInstructions} client={client} />
      );
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
