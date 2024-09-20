import React from "react";
import { Trash, SendHorizontal, Volume2 } from "lucide-react";
import {
  Button,
  Box,
  Flex,
  Text,
  Card,
  Badge,
  Menu,
  MenuButton,
  IconButton,
  MenuList,
  MenuItem,
} from "@chakra-ui/react";

const Message = ({ message, acceptMsg, rejectMsg, user, sayTTS }) => {
  const msg = {
    paddingLeft: "20px",
    paddingRight: "20px",
  };

  console.log(message);

  return (
    <Card>
      <Box>
        <Flex
          justifyContent={"space-between"}
          padding={"10px"}
          alignItems={"center"}
        >
          {message.is_accepted}
          {rejectMsg ? (
            <Button>
              <Trash onClick={rejectMsg} />
            </Button>
          ) : null}

          <Box flex={1} style={msg}>
            {user.name !== message.user ? (
              <Badge size="md">{message.user} </Badge>
            ) : null}
            <Text fontSize={"lg"}>
              {message.translated_text[user.language]
                ? message.translated_text[user.language]
                : message.text}
            </Text>
          </Box>
          {message.user === user.name && message.is_accepted ? (
            <TTSOptions message={message} sayTTS={sayTTS} />
          ) : null}
          {acceptMsg ? (
            <Button>
              <SendHorizontal onClick={acceptMsg} />
            </Button>
          ) : null}
        </Flex>
      </Box>
    </Card>
  );
};

const TTSOptions = ({ message, sayTTS }) => {
  return (
    <Menu>
      <MenuButton
        as={IconButton}
        aria-label="Options"
        icon={<Volume2 />}
        variant="outline"
        size={"lg"}
      />
      <MenuList>
        {Object.keys(message.translated_text).map((lang, i) => (
          <MenuItem onClick={() => sayTTS(message, lang)}>{lang}</MenuItem>
        ))}
      </MenuList>
    </Menu>
  );
};

export default Message;
