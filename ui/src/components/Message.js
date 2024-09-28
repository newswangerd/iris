import React, { useContext, useState } from "react";
import { Trash, SendHorizontal, Volume2, Edit, X } from "lucide-react";
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
  Textarea,
  Tag,
} from "@chakra-ui/react";

import { TranslationsContext } from "../context.js";

const Message = ({ message, acceptMsg, user, sayTTS }) => {
  const [editMode, setEditMode] = useState(false);
  const [editText, setEditText] = useState(message.text);
  const t = useContext(TranslationsContext);

  let handleInputChange = (e) => {
    let inputValue = e.target.value;
    setEditText(inputValue);
  };

  const msg = {
    paddingLeft: "20px",
    paddingRight: "20px",
  };

  const display = (
    <Text fontSize={"lg"}>
      {message.translated_text[user.language]
        ? message.translated_text[user.language]
        : message.text}
    </Text>
  );

  const leftButton = () => {
    if (message.user === user.name) {
      if (editMode) {
        return (
          <Button>
            <X onClick={() => setEditMode(false)} />
          </Button>
        );
      } else {
        return (
          <Button onClick={() => setEditMode(true)}>
            <Edit />
          </Button>
        );
      }
    }
  };

  const rightButton = () => {
    if (message.user === user.name) {
      if (editMode) {
        return (
          <Button
            onClick={() => {
              acceptMsg(message, editText);
              setEditMode(false);
            }}
          >
            <SendHorizontal />
          </Button>
        );
      } else {
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
                <MenuItem key={lang} onClick={() => sayTTS(message, lang)}>
                  {lang}
                </MenuItem>
              ))}
            </MenuList>
          </Menu>
        );
      }
    }
  };

  const edit = <Textarea onChange={handleInputChange} value={editText} />;

  return (
    <Card>
      <Box>
        <Flex
          justifyContent={"space-between"}
          padding={"10px"}
          alignItems={"center"}
        >
          {leftButton()}

          <Box flex={1} style={msg}>
            {user.name !== message.user ? (
              <Badge size="md">{message.user} </Badge>
            ) : null}

            {editMode ? edit : display}
            {message.original_text ? (
              <Tag size={"sm"}> {t("edited")} </Tag>
            ) : null}
          </Box>
          {rightButton()}
        </Flex>
      </Box>
    </Card>
  );
};

export default Message;
