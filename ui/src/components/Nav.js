import React, { useContext } from "react";
import {
  SquareMenu,
  CircleUser,
  Settings,
  LogOut,
  MessageCircleMore,
  Trash,
  QrCode,
} from "lucide-react";

import {
  Menu,
  MenuButton,
  IconButton,
  MenuList,
  MenuItem,
  useDisclosure,
} from "@chakra-ui/react";

import { UserContext, TranslationsContext } from "../context.js";
import QuickQR from "./QuickQR.js";

const Nav = ({ setView, client }) => {
  const user = useContext(UserContext);
  const t = useContext(TranslationsContext);

  const { isOpen, onOpen, onClose } = useDisclosure();

  if (!user) {
    return null;
  }

  const logout = (e) => {
    client.logout().then(() => setView("login"));
  };

  const clearMessages = (e) => {
    client.clear_recent_messages().then(() => {});
  };

  return (
    <>
      <QuickQR
        isOpen={isOpen}
        onOpen={onOpen}
        onClose={onClose}
        client={client}
      />
      <Menu>
        <MenuButton
          as={IconButton}
          aria-label="Options"
          icon={<SquareMenu />}
          variant="outline"
          size={"lg"}
        />
        <MenuList>
          <MenuItem isDisabled={true} icon={<CircleUser />}>
            {user.name}
          </MenuItem>
          {user.role === "admin" ? (
            <>
              <MenuItem
                icon={<MessageCircleMore />}
                onClick={() => setView("interpreter")}
              >
                {t("Interpreter")}
              </MenuItem>

              <MenuItem icon={<QrCode />} onClick={onOpen}>
                {t("Create QR Code")}
              </MenuItem>

              <MenuItem
                icon={<Settings />}
                onClick={() => setView("control_panel")}
              >
                {t("Control Panel")}
              </MenuItem>
              <MenuItem icon={<Trash />} onClick={clearMessages}>
                {t("Clear messages")}
              </MenuItem>
            </>
          ) : null}
          <MenuItem icon={<LogOut />} onClick={logout}>
            {t("Logout")}
          </MenuItem>
        </MenuList>
      </Menu>
    </>
  );
};

export default Nav;
