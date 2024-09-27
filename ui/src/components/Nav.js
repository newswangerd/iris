import React, { useContext } from "react";
import {
  SquareMenu,
  CircleUser,
  Settings,
  LogOut,
  MessageCircleMore,
} from "lucide-react";

import {
  Menu,
  MenuButton,
  IconButton,
  MenuList,
  MenuItem,
} from "@chakra-ui/react";

import { UserContext, TranslationsContext } from "../context.js";

const Nav = ({ setView, client }) => {
  const user = useContext(UserContext);
  const t = useContext(TranslationsContext);

  if (!user) {
    return null;
  }

  const logout = (e) => {
    client.logout().then(() => setView("login"));
  };

  return (
    <Menu>
      <MenuButton
        as={IconButton}
        aria-label="Options"
        icon={<SquareMenu />}
        variant="outline"
        size={"lg"}
      />
      <MenuList>
        <MenuItem disabled={true} icon={<CircleUser />}>
          {user.name}
        </MenuItem>
        {user.role === "admin" ? (
          <>
            <MenuItem
              icon={<MessageCircleMore />}
              onClick={() => setView("interpreter")}
            >
              {t("Interpeter")}
            </MenuItem>

            <MenuItem
              icon={<Settings />}
              onClick={() => setView("control_panel")}
            >
              {t("Control Panel")}
            </MenuItem>
          </>
        ) : null}
        <MenuItem icon={<LogOut />} onClick={logout}>
          {t("Logout")}
        </MenuItem>
      </MenuList>
    </Menu>
  );
};

export default Nav;
